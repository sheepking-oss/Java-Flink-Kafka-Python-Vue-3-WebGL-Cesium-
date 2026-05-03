package com.smartcity.kafka.generator;

import com.smartcity.common.model.BusGpsData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;

/**
 * 公交车 GPS 数据生成器
 * 模拟全市数千辆公交车主动推送 GPS 坐标
 */
public class BusGpsDataGenerator {
    private static final Logger logger = LoggerFactory.getLogger(BusGpsDataGenerator.class);
    private static final int TOTAL_BUSES = 5000;
    private static final int ACTIVE_BUSES = 3000;
    private static final double CITY_CENTER_LAT = 39.9042;
    private static final double CITY_CENTER_LNG = 116.4074;
    private static final double CITY_RADIUS = 0.1;

    private final List<BusInfo> buses;
    private final Random random;
    private final ScheduledExecutorService executorService;

    public interface DataCallback {
        void onDataGenerated(BusGpsData data);
    }

    private static class BusInfo {
        String busId;
        String routeId;
        double latitude;
        double longitude;
        double speed;
        double heading;
        boolean active;

        BusInfo(String busId, String routeId, double latitude, double longitude, double speed, double heading, boolean active) {
            this.busId = busId;
            this.routeId = routeId;
            this.latitude = latitude;
            this.longitude = longitude;
            this.speed = speed;
            this.heading = heading;
            this.active = active;
        }
    }

    public BusGpsDataGenerator() {
        this.buses = new ArrayList<>();
        this.random = new Random();
        this.executorService = Executors.newScheduledThreadPool(4);
        initializeBuses();
    }

    private void initializeBuses() {
        Set<Integer> activeBusIndices = new HashSet<>();
        while (activeBusIndices.size() < ACTIVE_BUSES) {
            activeBusIndices.add(random.nextInt(TOTAL_BUSES));
        }

        for (int i = 0; i < TOTAL_BUSES; i++) {
            String busId = String.format("BUS-%05d", i + 1);
            String routeId = String.format("ROUTE-%03d", random.nextInt(100) + 1);

            double angle = random.nextDouble() * 2 * Math.PI;
            double radius = random.nextDouble() * CITY_RADIUS;
            double lat = CITY_CENTER_LAT + radius * Math.cos(angle);
            double lng = CITY_CENTER_LNG + radius * Math.sin(angle);

            double speed = random.nextDouble() * 60 + 10;
            double heading = random.nextDouble() * 360;
            boolean active = activeBusIndices.contains(i);

            buses.add(new BusInfo(busId, routeId, lat, lng, speed, heading, active));
        }

        logger.info("Initialized {} buses, {} active", TOTAL_BUSES, ACTIVE_BUSES);
    }

    public void startGenerating(DataCallback callback, long intervalMs) {
        logger.info("Starting GPS data generation with interval {} ms", intervalMs);

        executorService.scheduleAtFixedRate(() -> {
            try {
                int generatedCount = 0;
                for (BusInfo bus : buses) {
                    if (bus.active) {
                        updateBusPosition(bus);
                        BusGpsData gpsData = createGpsData(bus);
                        callback.onDataGenerated(gpsData);
                        generatedCount++;
                    }
                }
                if (generatedCount > 0 && generatedCount % 1000 == 0) {
                    logger.debug("Generated {} GPS data points in this interval", generatedCount);
                }
            } catch (Exception e) {
                logger.error("Error generating GPS data", e);
            }
        }, 0, intervalMs, TimeUnit.MILLISECONDS);
    }

    private void updateBusPosition(BusInfo bus) {
        double speedKmh = bus.speed;
        double speedMs = speedKmh / 3.6;
        double distanceM = speedMs * 1.0;

        double latPerMeter = 1.0 / 111000.0;
        double lngPerMeter = 1.0 / (111000.0 * Math.cos(Math.toRadians(bus.latitude)));

        double headingRad = Math.toRadians(bus.heading);
        double dLat = distanceM * latPerMeter * Math.cos(headingRad);
        double dLng = distanceM * lngPerMeter * Math.sin(headingRad);

        bus.latitude += dLat;
        bus.longitude += dLng;

        double latChange = bus.latitude - CITY_CENTER_LAT;
        double lngChange = bus.longitude - CITY_CENTER_LNG;
        double distanceFromCenter = Math.sqrt(latChange * latChange + lngChange * lngChange);

        if (distanceFromCenter > CITY_RADIUS) {
            bus.heading = (bus.heading + 180 + ThreadLocalRandom.current().nextDouble(-45, 45)) % 360;
        } else {
            bus.heading += ThreadLocalRandom.current().nextDouble(-10, 10);
            if (bus.heading < 0) bus.heading += 360;
            if (bus.heading >= 360) bus.heading -= 360;
        }

        double speedChange = ThreadLocalRandom.current().nextDouble(-5, 5);
        bus.speed = Math.max(5, Math.min(80, bus.speed + speedChange));
    }

    private BusGpsData createGpsData(BusInfo bus) {
        return new BusGpsData(
                bus.busId,
                bus.routeId,
                bus.latitude,
                bus.longitude,
                bus.speed,
                bus.heading,
                Instant.now()
        );
    }

    public void stop() {
        logger.info("Stopping GPS data generator");
        executorService.shutdown();
        try {
            if (!executorService.awaitTermination(5, TimeUnit.SECONDS)) {
                executorService.shutdownNow();
            }
        } catch (InterruptedException e) {
            executorService.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}
