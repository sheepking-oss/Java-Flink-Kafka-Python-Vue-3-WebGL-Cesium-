package com.smartcity.flink.aggregator;

import com.smartcity.common.model.AggregatedGpsData;
import com.smartcity.common.model.BusGpsData;
import org.apache.flink.api.common.functions.AggregateFunction;
import org.apache.flink.api.java.tuple.Tuple3;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/**
 * GPS 数据聚合函数
 * 用于每秒钟聚合全市公交车 GPS 数据
 */
public class GpsDataAggregator implements AggregateFunction<BusGpsData, Tuple3<Integer, Double, List<BusGpsData>>, AggregatedGpsData> {

    @Override
    public Tuple3<Integer, Double, List<BusGpsData>> createAccumulator() {
        return new Tuple3<>(0, 0.0, new ArrayList<>());
    }

    @Override
    public Tuple3<Integer, Double, List<BusGpsData>> add(BusGpsData value, Tuple3<Integer, Double, List<BusGpsData>> accumulator) {
        accumulator.f0 += 1;
        accumulator.f1 += value.getSpeed();
        accumulator.f2.add(value);
        return accumulator;
    }

    @Override
    public AggregatedGpsData getResult(Tuple3<Integer, Double, List<BusGpsData>> accumulator) {
        AggregatedGpsData result = new AggregatedGpsData();
        result.setWindowStart(Instant.now().minusSeconds(1));
        result.setWindowEnd(Instant.now());
        result.setTotalBuses(5000);
        result.setActiveBuses(accumulator.f0);
        result.setAverageSpeed(accumulator.f0 > 0 ? accumulator.f1 / accumulator.f0 : 0.0);
        result.setBuses(accumulator.f2);
        return result;
    }

    @Override
    public Tuple3<Integer, Double, List<BusGpsData>> merge(Tuple3<Integer, Double, List<BusGpsData>> a, Tuple3<Integer, Double, List<BusGpsData>> b) {
        Tuple3<Integer, Double, List<BusGpsData>> merged = createAccumulator();
        merged.f0 = a.f0 + b.f0;
        merged.f1 = a.f1 + b.f1;
        merged.f2.addAll(a.f2);
        merged.f2.addAll(b.f2);
        return merged;
    }
}
