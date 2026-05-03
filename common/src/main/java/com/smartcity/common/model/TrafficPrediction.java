package com.smartcity.common.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;
import java.util.List;

/**
 * 交通拥堵预测结果模型
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class TrafficPrediction {
    @JsonProperty("prediction_id")
    private String predictionId;
    
    @JsonProperty("intersection_id")
    private String intersectionId;
    
    @JsonProperty("intersection_name")
    private String intersectionName;
    
    @JsonProperty("latitude")
    private double latitude;
    
    @JsonProperty("longitude")
    private double longitude;
    
    @JsonProperty("prediction_timestamp")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
    private Instant predictionTimestamp;
    
    @JsonProperty("prediction_window_minutes")
    private int predictionWindowMinutes;
    
    @JsonProperty("congestion_level")
    private CongestionLevel congestionLevel;
    
    @JsonProperty("confidence")
    private double confidence;
    
    @JsonProperty("predicted_bus_count")
    private int predictedBusCount;
    
    @JsonProperty("predicted_average_speed")
    private double predictedAverageSpeed;
    
    @JsonProperty("polygon_coordinates")
    private List<List<Double>> polygonCoordinates;
    
    @JsonProperty("is_glowing")
    private boolean isGlowing;

    public enum CongestionLevel {
        LOW,
        MEDIUM,
        HIGH,
        SEVERE
    }

    public TrafficPrediction() {
    }

    public TrafficPrediction(String predictionId, String intersectionId, String intersectionName, double latitude, double longitude, Instant predictionTimestamp, int predictionWindowMinutes, CongestionLevel congestionLevel, double confidence, int predictedBusCount, double predictedAverageSpeed, List<List<Double>> polygonCoordinates, boolean isGlowing) {
        this.predictionId = predictionId;
        this.intersectionId = intersectionId;
        this.intersectionName = intersectionName;
        this.latitude = latitude;
        this.longitude = longitude;
        this.predictionTimestamp = predictionTimestamp;
        this.predictionWindowMinutes = predictionWindowMinutes;
        this.congestionLevel = congestionLevel;
        this.confidence = confidence;
        this.predictedBusCount = predictedBusCount;
        this.predictedAverageSpeed = predictedAverageSpeed;
        this.polygonCoordinates = polygonCoordinates;
        this.isGlowing = isGlowing;
    }

    public String getPredictionId() {
        return predictionId;
    }

    public void setPredictionId(String predictionId) {
        this.predictionId = predictionId;
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

    public Instant getPredictionTimestamp() {
        return predictionTimestamp;
    }

    public void setPredictionTimestamp(Instant predictionTimestamp) {
        this.predictionTimestamp = predictionTimestamp;
    }

    public int getPredictionWindowMinutes() {
        return predictionWindowMinutes;
    }

    public void setPredictionWindowMinutes(int predictionWindowMinutes) {
        this.predictionWindowMinutes = predictionWindowMinutes;
    }

    public CongestionLevel getCongestionLevel() {
        return congestionLevel;
    }

    public void setCongestionLevel(CongestionLevel congestionLevel) {
        this.congestionLevel = congestionLevel;
    }

    public double getConfidence() {
        return confidence;
    }

    public void setConfidence(double confidence) {
        this.confidence = confidence;
    }

    public int getPredictedBusCount() {
        return predictedBusCount;
    }

    public void setPredictedBusCount(int predictedBusCount) {
        this.predictedBusCount = predictedBusCount;
    }

    public double getPredictedAverageSpeed() {
        return predictedAverageSpeed;
    }

    public void setPredictedAverageSpeed(double predictedAverageSpeed) {
        this.predictedAverageSpeed = predictedAverageSpeed;
    }

    public List<List<Double>> getPolygonCoordinates() {
        return polygonCoordinates;
    }

    public void setPolygonCoordinates(List<List<Double>> polygonCoordinates) {
        this.polygonCoordinates = polygonCoordinates;
    }

    public boolean isGlowing() {
        return isGlowing;
    }

    public void setGlowing(boolean glowing) {
        isGlowing = glowing;
    }

    @Override
    public String toString() {
        return "TrafficPrediction{" +
                "predictionId='" + predictionId + '\'' +
                ", intersectionId='" + intersectionId + '\'' +
                ", intersectionName='" + intersectionName + '\'' +
                ", latitude=" + latitude +
                ", longitude=" + longitude +
                ", predictionTimestamp=" + predictionTimestamp +
                ", predictionWindowMinutes=" + predictionWindowMinutes +
                ", congestionLevel=" + congestionLevel +
                ", confidence=" + confidence +
                ", predictedBusCount=" + predictedBusCount +
                ", predictedAverageSpeed=" + predictedAverageSpeed +
                ", polygonCoordinates=" + polygonCoordinates +
                ", isGlowing=" + isGlowing +
                '}';
    }
}
