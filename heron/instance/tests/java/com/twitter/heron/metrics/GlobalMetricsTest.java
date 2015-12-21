package com.twitter.heron.metrics;

import java.util.HashMap;
import java.util.Map;

import org.junit.Test;

import com.twitter.heron.api.generated.TopologyAPI;
import com.twitter.heron.api.metric.GlobalMetrics;
import com.twitter.heron.api.topology.TopologyContext;
import com.twitter.heron.common.core.base.WakeableLooper;
import com.twitter.heron.common.utils.metrics.MetricsCollector;
import com.twitter.heron.common.utils.topology.TopologyContextImpl;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

/**
 * Test for CounterFactory
 */
public class GlobalMetricsTest {
  // TODO: Use JMock framework for mock. (Needs extra jar)
  private static class FakeWakeableLooper extends WakeableLooper {
    protected void doWait() {
    }

    public void wakeUp() {
    }
  }

  @Test
  public void testGlobalMetrics() {
    MetricsCollector fakeCollector = new MetricsCollector(new FakeWakeableLooper(), null);
    TopologyContext fakeContext = new TopologyContextImpl(new HashMap<String, Object>(),
        TopologyAPI.Topology.getDefaultInstance(),
        new HashMap<Integer, String>(),
        0,
        fakeCollector);
    GlobalMetrics.init(fakeContext, 5);
    GlobalMetrics.incr("mycounter");
    Object value = GlobalMetrics.getUnderlyingCounter().getValueAndReset();
    assertTrue(value instanceof Map);
    Map metricsContent = (Map) value;
    assertTrue(metricsContent.containsKey("mycounter"));
    assertEquals(1, metricsContent.size());
    assertEquals(1L, metricsContent.get("mycounter"));

    // Increment two different counters
    GlobalMetrics.incr("mycounter1");
    GlobalMetrics.incr("mycounter2");
    GlobalMetrics.incr("mycounter1");
    metricsContent = (Map) GlobalMetrics.getUnderlyingCounter().getValueAndReset();
    assertTrue(metricsContent.containsKey("mycounter"));
    assertTrue(metricsContent.containsKey("mycounter1"));
    assertTrue(metricsContent.containsKey("mycounter2"));
    assertEquals(3L, metricsContent.size());
    assertEquals(0L, metricsContent.get("mycounter"));
    assertEquals(1L, metricsContent.get("mycounter2"));
    assertEquals(2L, metricsContent.get("mycounter1"));
  }
}