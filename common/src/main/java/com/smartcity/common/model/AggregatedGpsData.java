package com.smartcity.common.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;
import java.util.List;

/**
 * 聚合后的 GPS 数据模型
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class AggregatedGpsData {
    @JsonProperty("window_start")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
    private Instant windowStart;
    
    @JsonProperty("window_end")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
    private Instant windowEnd;
    
    @JsonProperty("total_buses")
    private int totalBuses;
    
    @JsonProperty("active_buses")
    private int activeBuses;
    
    @JsonProperty("average_speed")
    private double averageSpeed;
    
    @JsonProperty("buses")
    private List<BusGpsData> buses;

    public AggregatedGpsData() {
    }

    public AggregatedGpsData(Instant windowStart, Instant windowEnd, int totalBuses, int activeBuses, double averageSpeed, List<BusGpsData> buses) {
        this.windowStart = windowStart;
        this.windowEnd = windowEnd;
        this.totalBuses = totalBuses;
        this.activeBuses = activeBuses;
        this.averageSpeed = averageSpeed;
        this.buses = buses;
    }

    public Instant getWindowStart() {
        return windowStart;
    }

    public void setWindowStart(Instant windowStart) {
        this.windowStart = windowStart;
    }

    public Instant getWindowEnd() {
        return windowEnd;
    }

    public void setWindowEnd(Instant windowEnd) {
        this.windowEnd = windowEnd;
    }

    public int getTotalBuses() {
        return totalBuses;
    }

    public void setTotalBuses(int totalBuses) {
        this.totalBuses = totalBuses;
    }

    public int getActiveBuses() {
        return activeBuses;
    }

    public void setActiveBuses(int activeBuses) {
        this.activeBuses = activeBuses;
    }

    public double getAverageSpeed() {
        return averageSpeed;
    }

    public void setAverageSpeed(double averageSpeed) {
        this.averageSpeed = averageSpeed;
    }

    public List<BusGpsData> getBuses() {
        return buses;
    }

    public void setBuses(List<BusGpsData> buses) {
        this.buses = buses;
    }

    @Override
    public String toString() {
        return "AggregatedGpsData{" +
                "windowStart=" + windowStart +
                ", windowEnd=" + windowEnd +
                ", totalBuses=" + totalBuses +
                ", activeBuses=" + activeBuses +
                ", averageSpeed=" + averageSpeed +
                ", buses=" + buses +
                '}';
    }
}
