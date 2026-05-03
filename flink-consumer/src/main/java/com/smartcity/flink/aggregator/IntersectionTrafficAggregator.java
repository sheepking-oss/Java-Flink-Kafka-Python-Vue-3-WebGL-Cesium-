package com.smartcity.flink.aggregator;

import com.smartcity.common.model.BusGpsData;
import com.smartcity.common.model.IntersectionTrafficData;
import com.smartcity.flink.manager.IntersectionManager;
import com.smartcity.flink.model.IntersectionInfo;
import org.apache.flink.api.common.functions.AggregateFunction;
import org.apache.flink.api.java.tuple.Tuple4;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 十字路口交通数据聚合函数
 * 按十字路口聚合公交车 GPS 数据
 */
public class IntersectionTrafficAggregator implements AggregateFunction<BusGpsData, Tuple4<String, Integer, Double, List<String>>, IntersectionTrafficData> {

    @Override
    public Tuple4<String, Integer, Double, List<String>> createAccumulator() {
        return new Tuple4<>("", 0, 0.0, new ArrayList<>());
    }

    @Override
    public Tuple4<String, Integer, Double, List<String>> add(BusGpsData value, Tuple4<String, Integer, Double, List<String>> accumulator) {
        IntersectionManager manager = IntersectionManager.getInstance();
        Optional<IntersectionInfo> intersectionOpt = manager.findNearestIntersection(value.getLatitude(), value.getLongitude());

        if (intersectionOpt.isPresent()) {
            IntersectionInfo intersection = intersectionOpt.get();
            if (accumulator.f0.isEmpty()) {
                accumulator.f0 = intersection.getIntersectionId();
            }
            accumulator.f1 += 1;
            accumulator.f2 += value.getSpeed();
            accumulator.f3.add(value.getBusId());
        }
        return accumulator;
    }

    @Override
    public IntersectionTrafficData getResult(Tuple4<String, Integer, Double, List<String>> accumulator) {
        if (accumulator.f0.isEmpty()) {
            return null;
        }

        IntersectionManager manager = IntersectionManager.getInstance();
        Optional<IntersectionInfo> intersectionOpt = manager.getIntersectionById(accumulator.f0);

        if (intersectionOpt.isEmpty()) {
            return null;
        }

        IntersectionInfo intersection = intersectionOpt.get();
        IntersectionTrafficData result = new IntersectionTrafficData();
        result.setIntersectionId(intersection.getIntersectionId());
        result.setIntersectionName(intersection.getIntersectionName());
        result.setLatitude(intersection.getLatitude());
        result.setLongitude(intersection.getLongitude());
        result.setTimestamp(Instant.now());
        result.setBusCount(accumulator.f1);
        result.setAverageSpeed(accumulator.f1 > 0 ? accumulator.f2 / accumulator.f1 : 0.0);
        result.setBusIds(accumulator.f3);
        result.setPolygonCoordinates(intersection.getPolygonCoordinates());
        return result;
    }

    @Override
    public Tuple4<String, Integer, Double, List<String>> merge(Tuple4<String, Integer, Double, List<String>> a, Tuple4<String, Integer, Double, List<String>> b) {
        Tuple4<String, Integer, Double, List<String>> merged = createAccumulator();
        merged.f0 = a.f0.isEmpty() ? b.f0 : a.f0;
        merged.f1 = a.f1 + b.f1;
        merged.f2 = a.f2 + b.f2;
        merged.f3.addAll(a.f3);
        merged.f3.addAll(b.f3);
        return merged;
    }
}
