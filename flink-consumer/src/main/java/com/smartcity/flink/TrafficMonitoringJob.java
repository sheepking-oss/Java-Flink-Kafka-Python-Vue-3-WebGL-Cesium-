package com.smartcity.flink;

import com.smartcity.common.model.AggregatedGpsData;
import com.smartcity.common.model.BusGpsData;
import com.smartcity.common.model.IntersectionTrafficData;
import com.smartcity.common.util.JsonUtils;
import com.smartcity.flink.aggregator.GpsDataAggregator;
import com.smartcity.flink.aggregator.IntersectionTrafficAggregator;
import com.smartcity.flink.config.FlinkConfig;
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
import org.apache.flink.streaming.api.windowing.assigners.TumblingEventTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer;
import org.apache.flink.streaming.connectors.kafka.KafkaSerializationSchema;
import org.apache.flink.util.OutputTag;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.annotation.Nullable;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Optional;
import java.util.Properties;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 交通监控 Flink 主作业（优化版本）
 * 
 * 主要优化点：
 * 1. 从 ProcessingTime 切换到 EventTime 窗口，确保数据按事件时间正确聚合
 * 2. 水印延迟从 2 秒增加到 30 秒，允许 GPS 数据延迟到达
 * 3. 添加侧输出机制，收集并处理超过水印的延迟数据
 * 4. 延迟数据可以选择重新发送到主流程或单独处理
 * 5. 优化时间戳提取逻辑，支持处理时间回退
 */
public class TrafficMonitoringJob {
    private static final Logger logger = LoggerFactory.getLogger(TrafficMonitoringJob.class);
    
    private static final AtomicLong lateDataCount = new AtomicLong(0);
    private static final AtomicLong totalDataCount = new AtomicLong(0);
    
    private static final OutputTag<BusGpsData> LATE_DATA_TAG = 
            new OutputTag<BusGpsData>("late-gps-data") {};

    public static void main(String[] args) throws Exception {
        logger.info("==========================================");
        logger.info("  Smart City Traffic Monitoring System");
        logger.info("  Apache Flink Streaming Job (Optimized)");
        logger.info("==========================================");
        logger.info("Watermark Max OutOfOrderness: {} ms", FlinkConfig.getWatermarkMaxOutOfOrdernessMs());
        logger.info("Event Time Window: {} ms", FlinkConfig.getWindowEventTimeMs());
        logger.info("Fallback to Processing Time: {}", FlinkConfig.isFallbackToProcessingTime());
        logger.info("Late Data Forward to Main: {}", FlinkConfig.isLateDataForwardToMain());
        logger.info("==========================================");

        Configuration config = new Configuration();
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment(config);

        env.setParallelism(FlinkConfig.getParallelism());
        env.enableCheckpointing(FlinkConfig.getCheckpointInterval());
        
        env.getConfig().setAutoWatermarkInterval(200L);

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
                    } else {
                        totalDataCount.incrementAndGet();
                    }
                    return data;
                })
                .filter(data -> data != null && data.getBusId() != null)
                .name("JSON-Parse-and-Filter");

        long maxOutOfOrdernessMs = FlinkConfig.getWatermarkMaxOutOfOrdernessMs();
        boolean fallbackToProcessingTime = FlinkConfig.isFallbackToProcessingTime();

        WatermarkStrategy<BusGpsData> watermarkStrategy = WatermarkStrategy
                .<BusGpsData>forBoundedOutOfOrderness(Duration.ofMillis(maxOutOfOrdernessMs))
                .withTimestampAssigner((event, timestamp) -> {
                    if (event.getTimestamp() != null) {
                        return event.getTimestamp().toEpochMilli();
                    }
                    if (fallbackToProcessingTime) {
                        long currentTime = System.currentTimeMillis();
                        if (logger.isDebugEnabled()) {
                            logger.debug("Bus {} has no timestamp, using processing time: {}", 
                                    event.getBusId(), currentTime);
                        }
                        return currentTime;
                    }
                    return timestamp;
                })
                .withIdleness(Duration.ofSeconds(5));

        SingleOutputStreamOperator<BusGpsData> timedStream = gpsStream
                .assignTimestampsAndWatermarks(watermarkStrategy)
                .name("Timestamp-and-Watermark-Assigner");

        long windowSizeMs = FlinkConfig.getWindowEventTimeMs();
        boolean forwardLateData = FlinkConfig.isLateDataForwardToMain();

        SingleOutputStreamOperator<AggregatedGpsData> aggregatedStream = timedStream
                .windowAll(TumblingEventTimeWindows.of(Time.milliseconds(windowSizeMs)))
                .sideOutputLateData(LATE_DATA_TAG)
                .aggregate(new GpsDataAggregator())
                .name("GPS-Data-Aggregation-EventTime");

        DataStream<BusGpsData> lateStream = aggregatedStream.getSideOutput(LATE_DATA_TAG);

        lateStream.process(new org.apache.flink.streaming.api.functions.ProcessFunction<BusGpsData, BusGpsData>() {
            @Override
            public void processElement(BusGpsData value, Context ctx, org.apache.flink.util.Collector<BusGpsData> out) throws Exception {
                long lateCount = lateDataCount.incrementAndGet();
                long currentWatermark = ctx.timerService().currentWatermark();
                long eventTime = value.getTimestamp() != null ? 
                        value.getTimestamp().toEpochMilli() : System.currentTimeMillis();
                
                if (lateCount % 100 == 0) {
                    logger.warn("Received late data - Bus: {}, EventTime: {}, CurrentWatermark: {}, TotalLate: {}, Total: {}",
                            value.getBusId(), eventTime, currentWatermark, lateCount, totalDataCount.get());
                }
                
                if (forwardLateData) {
                    out.collect(value);
                }
            }
        }).name("Late-Data-Logger");

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

        SingleOutputStreamOperator<IntersectionTrafficData> intersectionStream = timedStream
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
                .window(TumblingEventTimeWindows.of(Time.milliseconds(windowSizeMs)))
                .sideOutputLateData(new OutputTag<BusGpsData>("late-intersection-data") {})
                .aggregate(new IntersectionTrafficAggregator())
                .filter(data -> data != null)
                .name("Intersection-Traffic-Aggregation-EventTime");

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

        env.addSource(new org.apache.flink.streaming.api.functions.source.RichSourceFunction<String>() {
            private volatile boolean running = true;
            
            @Override
            public void run(SourceContext<String> ctx) throws Exception {
                while (running) {
                    Thread.sleep(60000);
                    logger.info("Flink Job Statistics - Total Data: {}, Late Data: {}, Late Rate: {}%",
                            totalDataCount.get(),
                            lateDataCount.get(),
                            totalDataCount.get() > 0 ? 
                                    String.format("%.2f", (double) lateDataCount.get() * 100 / totalDataCount.get()) : "0.00");
                }
            }
            
            @Override
            public void cancel() {
                running = false;
            }
        }).name("Statistics-Logger");

        logger.info("Starting Flink job: {}", FlinkConfig.getJobName());
        env.execute(FlinkConfig.getJobName());
    }
}
