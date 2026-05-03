package com.smartcity.flink;

import com.smartcity.common.model.AggregatedGpsData;
import com.smartcity.common.model.BusGpsData;
import com.smartcity.common.model.IntersectionTrafficData;
import com.smartcity.common.util.JsonUtils;
import com.smartcity.flink.aggregator.GpsDataAggregator;
import com.smartcity.flink.aggregator.IntersectionTrafficAggregator;
import com.smartcity.flink.config.FlinkConfig;
import com.smartcity.flink.function.BusGpsTimestampExtractor;
import com.smartcity.flink.manager.IntersectionManager;
import com.smartcity.flink.model.IntersectionInfo;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.api.java.functions.KeySelector;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.datastream.SingleOutputStreamOperator;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.assigners.TumblingProcessingTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer;
import org.apache.flink.streaming.connectors.kafka.KafkaSerializationSchema;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.annotation.Nullable;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.Properties;

/**
 * 交通监控 Flink 主作业
 * 从 Kafka 消费公交车 GPS 数据，每秒实时聚合，并输出聚合结果
 */
public class TrafficMonitoringJob {
    private static final Logger logger = LoggerFactory.getLogger(TrafficMonitoringJob.class);

    public static void main(String[] args) throws Exception {
        logger.info("==========================================");
        logger.info("  Smart City Traffic Monitoring System");
        logger.info("  Apache Flink Streaming Job");
        logger.info("==========================================");

        Configuration config = new Configuration();
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment(config);

        env.setParallelism(FlinkConfig.getParallelism());
        env.enableCheckpointing(FlinkConfig.getCheckpointInterval());

        logger.info("Flink environment configured with parallelism: {}", FlinkConfig.getParallelism());

        Properties consumerProps = FlinkConfig.getKafkaConsumerProperties();
        FlinkKafkaConsumer<String> kafkaConsumer = new FlinkKafkaConsumer<>(
                FlinkConfig.getBusGpsTopic(),
                new SimpleStringSchema(),
                consumerProps
        );

        String offsetReset = FlinkConfig.getAutoOffsetReset();
        if ("earliest".equals(offsetReset)) {
            kafkaConsumer.setStartFromEarliest();
        } else {
            kafkaConsumer.setStartFromLatest();
        }

        DataStream<String> rawStream = env.addSource(kafkaConsumer).name("Kafka-GPS-Consumer");

        SingleOutputStreamOperator<BusGpsData> gpsStream = rawStream
                .map((MapFunction<String, BusGpsData>) json -> {
                    BusGpsData data = JsonUtils.fromJson(json, BusGpsData.class);
                    if (data == null) {
                        logger.warn("Failed to parse GPS data: {}", json);
                    }
                    return data;
                })
                .filter(data -> data != null && data.getBusId() != null)
                .name("JSON-Parse-and-Filter");

        SingleOutputStreamOperator<BusGpsData> timedStream = gpsStream
                .assignTimestampsAndWatermarks(
                        WatermarkStrategy.<BusGpsData>forBoundedOutOfOrderness(Time.seconds(2))
                                .withTimestampAssigner((event, timestamp) -> {
                                    if (event.getTimestamp() != null) {
                                        return event.getTimestamp().toEpochMilli();
                                    }
                                    return System.currentTimeMillis();
                                })
                )
                .name("Timestamp-Assigner");

        DataStream<AggregatedGpsData> aggregatedStream = timedStream
                .windowAll(TumblingProcessingTimeWindows.of(Time.seconds(1)))
                .aggregate(new GpsDataAggregator())
                .name("GPS-Data-Aggregation");

        DataStream<String> aggregatedJsonStream = aggregatedStream
                .map((MapFunction<AggregatedGpsData, String>) JsonUtils::toJson)
                .filter(json -> json != null && !json.isEmpty())
                .name("Aggregated-JSON-Serialization");

        Properties producerProps = FlinkConfig.getKafkaProducerProperties();
        FlinkKafkaProducer<String> aggregatedProducer = new FlinkKafkaProducer<>(
                FlinkConfig.getAggregatedGpsTopic(),
                new KafkaSerializationSchema<String>() {
                    @Override
                    public ProducerRecord<byte[], byte[]> serialize(String element, @Nullable Long timestamp) {
                        return new ProducerRecord<>(
                                FlinkConfig.getAggregatedGpsTopic(),
                                element.getBytes(StandardCharsets.UTF_8)
                        );
                    }
                },
                producerProps,
                FlinkKafkaProducer.Semantic.AT_LEAST_ONCE
        );

        aggregatedJsonStream.addSink(aggregatedProducer).name("Aggregated-Kafka-Producer");

        DataStream<IntersectionTrafficData> intersectionStream = timedStream
                .filter(data -> {
                    IntersectionManager manager = IntersectionManager.getInstance();
                    Optional<IntersectionInfo> intersectionOpt = manager.findNearestIntersection(
                            data.getLatitude(), data.getLongitude()
                    );
                    return intersectionOpt.isPresent();
                })
                .keyBy((KeySelector<BusGpsData, String>) data -> {
                    IntersectionManager manager = IntersectionManager.getInstance();
                    Optional<IntersectionInfo> intersectionOpt = manager.findNearestIntersection(
                            data.getLatitude(), data.getLongitude()
                    );
                    return intersectionOpt.map(IntersectionInfo::getIntersectionId).orElse("UNKNOWN");
                })
                .window(TumblingProcessingTimeWindows.of(Time.seconds(1)))
                .aggregate(new IntersectionTrafficAggregator())
                .filter(data -> data != null)
                .name("Intersection-Traffic-Aggregation");

        DataStream<String> intersectionJsonStream = intersectionStream
                .map((MapFunction<IntersectionTrafficData, String>) JsonUtils::toJson)
                .filter(json -> json != null && !json.isEmpty())
                .name("Intersection-JSON-Serialization");

        FlinkKafkaProducer<String> intersectionProducer = new FlinkKafkaProducer<>(
                FlinkConfig.getIntersectionTrafficTopic(),
                new KafkaSerializationSchema<String>() {
                    @Override
                    public ProducerRecord<byte[], byte[]> serialize(String element, @Nullable Long timestamp) {
                        return new ProducerRecord<>(
                                FlinkConfig.getIntersectionTrafficTopic(),
                                element.getBytes(StandardCharsets.UTF_8)
                        );
                    }
                },
                producerProps,
                FlinkKafkaProducer.Semantic.AT_LEAST_ONCE
        );

        intersectionJsonStream.addSink(intersectionProducer).name("Intersection-Kafka-Producer");

        aggregatedStream.print("Aggregated GPS Data: ");
        intersectionStream.print("Intersection Traffic Data: ");

        logger.info("Starting Flink job: {}", FlinkConfig.getJobName());
        env.execute(FlinkConfig.getJobName());
    }
}
