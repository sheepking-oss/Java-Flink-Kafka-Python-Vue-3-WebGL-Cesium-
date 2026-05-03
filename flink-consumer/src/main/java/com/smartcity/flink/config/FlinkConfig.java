package com.smartcity.flink.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Flink 配置类（优化版本）
 * 新增时间窗口、水印延迟、延迟数据处理等配置
 */
public class FlinkConfig {
    private static final Logger logger = LoggerFactory.getLogger(FlinkConfig.class);
    private static final Properties properties = new Properties();

    static {
        try (InputStream inputStream = FlinkConfig.class.getClassLoader().getResourceAsStream("flink.properties")) {
            if (inputStream != null) {
                properties.load(inputStream);
                logger.info("Successfully loaded flink.properties");
            } else {
                logger.warn("flink.properties not found, using default values");
                setDefaultProperties();
            }
        } catch (IOException e) {
            logger.error("Failed to load flink.properties, using default values", e);
            setDefaultProperties();
        }
    }

    private static void setDefaultProperties() {
        properties.setProperty("flink.job.name", "TrafficMonitoringJob");
        properties.setProperty("flink.parallelism", "2");
        properties.setProperty("flink.checkpoint.interval", "60000");
        
        properties.setProperty("flink.watermark.max.outoforderness.ms", "30000");
        properties.setProperty("flink.window.event.time.ms", "1000");
        properties.setProperty("flink.window.fallback.to.processing.time", "true");
        
        properties.setProperty("flink.late.data.tag", "late-gps-data");
        properties.setProperty("flink.late.data.forward.to.main", "true");
        properties.setProperty("flink.late.data.log.level", "DEBUG");
        
        properties.setProperty("kafka.bootstrap.servers", "localhost:9092");
        properties.setProperty("kafka.topic.bus.gps", "bus-gps-data");
        properties.setProperty("kafka.topic.aggregated.gps", "aggregated-gps-data");
        properties.setProperty("kafka.topic.intersection.traffic", "intersection-traffic-data");
        properties.setProperty("kafka.topic.late.gps", "late-gps-data");
        properties.setProperty("kafka.consumer.group.id", "flink-traffic-group");
        properties.setProperty("kafka.consumer.auto.offset.reset", "latest");
    }

    public static String getJobName() {
        return properties.getProperty("flink.job.name", "TrafficMonitoringJob");
    }

    public static int getParallelism() {
        return Integer.parseInt(properties.getProperty("flink.parallelism", "2"));
    }

    public static long getCheckpointInterval() {
        return Long.parseLong(properties.getProperty("flink.checkpoint.interval", "60000"));
    }

    public static long getWatermarkMaxOutOfOrdernessMs() {
        return Long.parseLong(properties.getProperty("flink.watermark.max.outoforderness.ms", "30000"));
    }

    public static long getWindowEventTimeMs() {
        return Long.parseLong(properties.getProperty("flink.window.event.time.ms", "1000"));
    }

    public static boolean isFallbackToProcessingTime() {
        return Boolean.parseBoolean(properties.getProperty("flink.window.fallback.to.processing.time", "true"));
    }

    public static String getLateDataTag() {
        return properties.getProperty("flink.late.data.tag", "late-gps-data");
    }

    public static boolean isLateDataForwardToMain() {
        return Boolean.parseBoolean(properties.getProperty("flink.late.data.forward.to.main", "true"));
    }

    public static String getLateDataLogLevel() {
        return properties.getProperty("flink.late.data.log.level", "DEBUG");
    }

    public static String getBootstrapServers() {
        return properties.getProperty("kafka.bootstrap.servers", "localhost:9092");
    }

    public static String getBusGpsTopic() {
        return properties.getProperty("kafka.topic.bus.gps", "bus-gps-data");
    }

    public static String getAggregatedGpsTopic() {
        return properties.getProperty("kafka.topic.aggregated.gps", "aggregated-gps-data");
    }

    public static String getIntersectionTrafficTopic() {
        return properties.getProperty("kafka.topic.intersection.traffic", "intersection-traffic-data");
    }

    public static String getLateGpsTopic() {
        return properties.getProperty("kafka.topic.late.gps", "late-gps-data");
    }

    public static String getConsumerGroupId() {
        return properties.getProperty("kafka.consumer.group.id", "flink-traffic-group");
    }

    public static String getAutoOffsetReset() {
        return properties.getProperty("kafka.consumer.auto.offset.reset", "latest");
    }

    public static Properties getKafkaConsumerProperties() {
        Properties consumerProps = new Properties();
        consumerProps.setProperty("bootstrap.servers", getBootstrapServers());
        consumerProps.setProperty("group.id", getConsumerGroupId());
        consumerProps.setProperty("auto.offset.reset", getAutoOffsetReset());
        return consumerProps;
    }

    public static Properties getKafkaProducerProperties() {
        Properties producerProps = new Properties();
        producerProps.setProperty("bootstrap.servers", getBootstrapServers());
        return producerProps;
    }
}
