package com.smartcity.flink.function;

import com.smartcity.common.model.BusGpsData;
import org.apache.flink.streaming.api.functions.timestamps.BoundedOutOfOrdernessTimestampExtractor;
import org.apache.flink.streaming.api.windowing.time.Time;

/**
 * 时间戳提取器
 * 从 BusGpsData 中提取时间戳并生成水印
 */
public class BusGpsTimestampExtractor extends BoundedOutOfOrdernessTimestampExtractor<BusGpsData> {

    public BusGpsTimestampExtractor(Time maxOutOfOrderness) {
        super(maxOutOfOrderness);
    }

    @Override
    public long extractTimestamp(BusGpsData element) {
        if (element.getTimestamp() != null) {
            return element.getTimestamp().toEpochMilli();
        }
        return System.currentTimeMillis();
    }
}
