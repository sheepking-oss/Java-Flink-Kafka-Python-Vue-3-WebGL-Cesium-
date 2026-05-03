package com.smartcity.common.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;
import java.util.List;

/**
 * 十字路口交通数据模型
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class IntersectionTrafficData {
    @JsonProperty("intersection_id")
    private String intersectionId;
    
    @JsonProperty("intersection_name")
    private String intersectionName;
    
    @JsonProperty("latitude")
    private double latitude;
    
    @JsonProperty("longitude")
    private double longitude;
    
    @JsonProperty("timestamp")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
    private Instant timestamp;
    
    @JsonProperty("bus_count")
    private int busCount;
    
    @JsonProperty("average_speed")
    private double averageSpeed;
    
    @JsonProperty("bus_ids")
    private List<String> busIds;
    
    @JsonProperty("polygon_coordinates")
    private List<List<Double>> polygonCoordinates;

    public IntersectionTrafficData() {
    }

    public IntersectionTrafficData(String intersectionId, String intersectionName, double latitude, double longitude, Instant timestamp, int busCount, double averageSpeed, List<String> busIds, List<List<Double>> polygonCoordinates) {
        this.intersectionId = intersectionId;
        this.intersectionName = intersectionName;
        this.latitude = latitude;
        this.longitude = longitude;
        this.timestamp = timestamp;
        this.busCount = busCount;
        this.averageSpeed = averageSpeed;
        this.busIds = busIds;
        this.polygonCoordinates = polygonCoordinates;
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

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    public int getBusCount() {
        return busCount;
    }

    public void setBusCount(int busCount) {
        this.busCount = busCount;
    }

    public double getAverageSpeed() {
        return averageSpeed;
    }

    public void setAverageSpeed(double averageSpeed) {
        this.averageSpeed = averageSpeed;
    }

    public List<String> getBusIds() {
        return busIds;
    }

    public void setBusIds(List<String> busIds) {
        this.busIds = busIds;
    }

    public List<List<Double>> getPolygonCoordinates() {
        return polygonCoordinates;
    }

    public void setPolygonCoordinates(List<List<Double>> polygonCoordinates) {
        this.polygonCoordinates = polygonCoordinates;
    }

    @Override
    public String toString() {
        return "IntersectionTrafficData{" +
                "intersectionId='" + intersectionId + '\'' +
                ", intersectionName='" + intersectionName + '\'' +
                ", latitude=" + latitude +
                ", longitude=" + longitude +
                ", timestamp=" + timestamp +
                ", busCount=" + busCount +
                ", averageSpeed=" + averageSpeed +
                ", busIds=" + busIds +
                ", polygonCoordinates=" + polygonCoordinates +
                '}';
    }
}
