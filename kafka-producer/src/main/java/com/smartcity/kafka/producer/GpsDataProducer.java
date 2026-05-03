package com.smartcity.kafka.producer;

import com.smartcity.common.model.BusGpsData;
import com.smartcity.common.util.JsonUtils;
import com.smartcity.kafka.config.KafkaConfig;
import com.smartcity.kafka.generator.BusGpsDataGenerator;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.clients.producer.RecordMetadata;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Properties;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Kafka Producer 主类
 * 负责将生成的 GPS 数据发送到 Kafka 集群
 */
public class GpsDataProducer {
    private static final Logger logger = LoggerFactory.getLogger(GpsDataProducer.class);
    private static final AtomicLong messageCount = new AtomicLong(0);
    private static final AtomicLong errorCount = new AtomicLong(0);

    private final KafkaProducer<String, String> producer;
    private final BusGpsDataGenerator generator;
    private final String topic;
    private volatile boolean running;

    public GpsDataProducer() {
        Properties producerProps = KafkaConfig.getKafkaProducerProperties();
        this.producer = new KafkaProducer<>(producerProps);
        this.generator = new BusGpsDataGenerator();
        this.topic = KafkaConfig.getBusGpsTopic();
        this.running = true;
        logger.info("Kafka Producer initialized with topic: {}", topic);
    }

    public void start() {
        logger.info("Starting GPS data producer...");
        
        generator.startGenerating(this::sendData, 1000);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info("Shutdown hook triggered, stopping producer...");
            stop();
        }));

        while (running) {
            try {
                Thread.sleep(10000);
                logger.info("Producer statistics - Total messages: {}, Errors: {}",
                        messageCount.get(), errorCount.get());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                logger.info("Producer thread interrupted");
                break;
            }
        }
    }

    private void sendData(BusGpsData data) {
        try {
            String jsonData = JsonUtils.toJson(data);
            ProducerRecord<String, String> record = new ProducerRecord<>(topic, data.getBusId(), jsonData);
            
            Future<RecordMetadata> future = producer.send(record, (metadata, exception) -> {
                if (exception != null) {
                    errorCount.incrementAndGet();
                    logger.error("Failed to send message for bus: {}", data.getBusId(), exception);
                } else {
                    long count = messageCount.incrementAndGet();
                    if (count % 10000 == 0) {
                        logger.info("Successfully sent {} messages", count);
                    }
                }
            });

        } catch (Exception e) {
            errorCount.incrementAndGet();
            logger.error("Error preparing message for bus: {}", data.getBusId(), e);
        }
    }

    public void stop() {
        logger.info("Stopping GPS data producer...");
        running = false;
        
        try {
            generator.stop();
        } catch (Exception e) {
            logger.error("Error stopping generator", e);
        }
        
        try {
            producer.flush();
            producer.close();
        } catch (Exception e) {
            logger.error("Error closing producer", e);
        }
        
        logger.info("GPS data producer stopped. Final statistics - Total messages: {}, Errors: {}",
                messageCount.get(), errorCount.get());
    }

    public static void main(String[] args) {
        logger.info("==========================================");
        logger.info("  Smart City Traffic Monitoring System");
        logger.info("  Kafka GPS Data Producer");
        logger.info("==========================================");
        
        GpsDataProducer producer = new GpsDataProducer();
        
        try {
            producer.start();
        } catch (Exception e) {
            logger.error("Producer failed", e);
            System.exit(1);
        }
    }
}
