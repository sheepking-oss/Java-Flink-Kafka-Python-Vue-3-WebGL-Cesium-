package com.smartcity.kafka.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Kafka 配置类
 */
public class KafkaConfig {
    private static final Logger logger = LoggerFactory.getLogger(KafkaConfig.class);
    private static final Properties properties = new Properties();

    static {
        try (InputStream inputStream = KafkaConfig.class.getClassLoader().getResourceAsStream("kafka.properties")) {
            if (inputStream != null) {
                properties.load(inputStream);
                logger.info("Successfully loaded kafka.properties");
            } else {
                logger.warn("kafka.properties not found, using default values");
                setDefaultProperties();
            }
        } catch (IOException e) {
            logger.error("Failed to load kafka.properties, using default values", e);
            setDefaultProperties();
        }
    }

    private static void setDefaultProperties() {
        properties.setProperty("kafka.bootstrap.servers", "localhost:9092");
        properties.setProperty("kafka.topic.bus.gps", "bus-gps-data");
        properties.setProperty("kafka.topic.aggregated.gps", "aggregated-gps-data");
        properties.setProperty("kafka.topic.intersection.traffic", "intersection-traffic-data");
        properties.setProperty("kafka.topic.traffic.prediction", "traffic-prediction-data");
        properties.setProperty("kafka.producer.acks", "1");
        properties.setProperty("kafka.producer.retries", "3");
        properties.setProperty("kafka.producer.batch.size", "16384");
        properties.setProperty("kafka.producer.linger.ms", "1");
        properties.setProperty("kafka.producer.buffer.memory", "33554432");
        properties.setProperty("kafka.producer.key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.setProperty("kafka.producer.value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
    }

    public static Properties getKafkaProducerProperties() {
        Properties producerProps = new Properties();
        producerProps.put("bootstrap.servers", getBootstrapServers());
        producerProps.put("acks", properties.getProperty("kafka.producer.acks", "1"));
        producerProps.put("retries", Integer.parseInt(properties.getProperty("kafka.producer.retries", "3")));
        producerProps.put("batch.size", Integer.parseInt(properties.getProperty("kafka.producer.batch.size", "16384")));
        producerProps.put("linger.ms", Long.parseLong(properties.getProperty("kafka.producer.linger.ms", "1")));
        producerProps.put("buffer.memory", Long.parseLong(properties.getProperty("kafka.producer.buffer.memory", "33554432")));
        producerProps.put("key.serializer", properties.getProperty("kafka.producer.key.serializer", "org.apache.kafka.common.serialization.StringSerializer"));
        producerProps.put("value.serializer", properties.getProperty("kafka.producer.value.serializer", "org.apache.kafka.common.serialization.StringSerializer"));
        return producerProps;
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

    public static String getTrafficPredictionTopic() {
        return properties.getProperty("kafka.topic.traffic.prediction", "traffic-prediction-data");
    }
}
