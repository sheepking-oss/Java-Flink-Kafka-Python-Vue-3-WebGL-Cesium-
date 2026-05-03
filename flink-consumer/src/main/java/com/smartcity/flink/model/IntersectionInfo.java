package com.smartcity.flink.model;

import java.util.ArrayList;
import java.util.List;

/**
 * 十字路口信息模型
 */
public class IntersectionInfo {
    private String intersectionId;
    private String intersectionName;
    private double latitude;
    private double longitude;
    private double radius;
    private List<List<Double>> polygonCoordinates;

    public IntersectionInfo() {
    }

    public IntersectionInfo(String intersectionId, String intersectionName, double latitude, double longitude, double radius) {
        this.intersectionId = intersectionId;
        this.intersectionName = intersectionName;
        this.latitude = latitude;
        this.longitude = longitude;
        this.radius = radius;
        this.polygonCoordinates = generatePolygon(latitude, longitude, radius);
    }

    private List<List<Double>> generatePolygon(double lat, double lng, double radius) {
        List<List<Double>> polygon = new ArrayList<>();
        int sides = 8;
        double latPerMeter = 1.0 / 111000.0;
        double lngPerMeter = 1.0 / (111000.0 * Math.cos(Math.toRadians(lat)));

        for (int i = 0; i < sides; i++) {
            double angle = 2 * Math.PI * i / sides;
            double dLat = radius * latPerMeter * Math.cos(angle);
            double dLng = radius * lngPerMeter * Math.sin(angle);
            List<Double> point = new ArrayList<>();
            point.add(lng + dLng);
            point.add(lat + dLat);
            polygon.add(point);
        }
        
        if (!polygon.isEmpty()) {
            polygon.add(polygon.get(0));
        }
        return polygon;
    }

    public String getIntersectionId() {
        return intersectionId;
    }

    public void setIntersectionId(String intersectionId) {
        this.intersectionId = intersectionId;
    }

    public String getIntersectionName() {
        return intersectionName;
    }

    public void setIntersectionName(String intersectionName) {
        this.intersectionName = intersectionName;
    }

    public double getLatitude() {
        return latitude;
    }

    public void setLatitude(double latitude) {
        this.latitude = latitude;
    }

    public double getLongitude() {
        return longitude;
    }

    public void setLongitude(double longitude) {
        this.longitude = longitude;
    }

    public double getRadius() {
        return radius;
    }

    public void setRadius(double radius) {
        this.radius = radius;
    }

    public List<List<Double>> getPolygonCoordinates() {
        return polygonCoordinates;
    }

    public void setPolygonCoordinates(List<List<Double>> polygonCoordinates) {
        this.polygonCoordinates = polygonCoordinates;
    }

    @Override
    public String toString() {
        return "IntersectionInfo{" +
                "intersectionId='" + intersectionId + '\'' +
                ", intersectionName='" + intersectionName + '\'' +
                ", latitude=" + latitude +
                ", longitude=" + longitude +
                ", radius=" + radius +
                '}';
    }
}
