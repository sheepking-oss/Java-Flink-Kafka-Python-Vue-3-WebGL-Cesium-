package com.smartcity.flink.manager;

import com.smartcity.flink.model.IntersectionInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 十字路口管理器
 * 管理全市十字路口信息，并提供根据 GPS 坐标查找最近十字路口的功能
 */
public class IntersectionManager {
    private static final Logger logger = LoggerFactory.getLogger(IntersectionManager.class);
    private static final IntersectionManager INSTANCE = new IntersectionManager();
    private final List<IntersectionInfo> intersections;

    private IntersectionManager() {
        this.intersections = new ArrayList<>();
        initializeIntersections();
    }

    public static IntersectionManager getInstance() {
        return INSTANCE;
    }

    private void initializeIntersections() {
        intersections.add(new IntersectionInfo("INT-001", "天安门东", 39.9060, 116.4090, 150));
        intersections.add(new IntersectionInfo("INT-002", "天安门西", 39.9060, 116.4020, 150));
        intersections.add(new IntersectionInfo("INT-003", "王府井", 39.9100, 116.4110, 150));
        intersections.add(new IntersectionInfo("INT-004", "前门", 39.8980, 116.4050, 150));
        intersections.add(new IntersectionInfo("INT-005", "建国门", 39.9080, 116.4350, 150));
        intersections.add(new IntersectionInfo("INT-006", "复兴门", 39.9080, 116.3620, 150));
        intersections.add(new IntersectionInfo("INT-007", "西单", 39.9120, 116.3710, 150));
        intersections.add(new IntersectionInfo("INT-008", "东单", 39.9120, 116.4210, 150));
        intersections.add(new IntersectionInfo("INT-009", "朝阳门", 39.9230, 116.4320, 150));
        intersections.add(new IntersectionInfo("INT-010", "阜成门", 39.9230, 116.3560, 150));

        logger.info("Initialized {} intersections", intersections.size());
    }

    /**
     * 根据 GPS 坐标查找最近的十字路口
     */
    public Optional<IntersectionInfo> findNearestIntersection(double latitude, double longitude) {
        IntersectionInfo nearest = null;
        double minDistance = Double.MAX_VALUE;

        for (IntersectionInfo intersection : intersections) {
            double distance = calculateDistance(latitude, longitude, intersection.getLatitude(), intersection.getLongitude());
            if (distance < minDistance) {
                minDistance = distance;
                nearest = intersection;
            }
        }

        if (nearest != null && minDistance <= nearest.getRadius()) {
            return Optional.of(nearest);
        }

        return Optional.empty();
    }

    /**
     * 计算两点之间的距离（米）
     * 使用 Haversine 公式
     */
    private double calculateDistance(double lat1, double lng1, double lat2, double lng2) {
        double earthRadius = 6371000;
        double dLat = Math.toRadians(lat2 - lat1);
        double dLng = Math.toRadians(lng2 - lng1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                        Math.sin(dLng / 2) * Math.sin(dLng / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return earthRadius * c;
    }

    /**
     * 获取所有十字路口信息
     */
    public List<IntersectionInfo> getAllIntersections() {
        return new ArrayList<>(intersections);
    }

    /**
     * 根据 ID 获取十字路口信息
     */
    public Optional<IntersectionInfo> getIntersectionById(String id) {
        return intersections.stream()
                .filter(i -> i.getIntersectionId().equals(id))
                .findFirst();
    }
}
