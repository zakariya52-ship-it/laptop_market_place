import { describe, expect, it } from "vitest";
import { buildPredictionPayload } from "./api";

describe("prediction payload", () => {
  it("preserves the FastAPI field names and derived storage total", () => {
    const payload = buildPredictionPayload({
      company: "lenovo",
      type_name: "thinkpad",
      inches: "14",
      resolution: "WUXGA (1920x1200)",
      cpu: "intel_core_i7",
      gpu: "intel_iris",
      os: "windows",
      touch_screen: "1",
      ips: "0",
      dedicated_gpu: "0",
      ram_gb: "16",
      weight_kg: "1.35",
      x_res: "1920",
      y_res: "1200",
      ppi: "161",
      ssd: "512",
      hhd: "0",
      storage_type: "ssd_only",
      storage_category: "standard_(512gb-1tb)",
    });

    expect(payload).toEqual({
      company: "lenovo",
      type_name: "thinkpad",
      inches: 14,
      screen_resolution: "1920_x_1200",
      cpu: "intel_core_i7",
      gpu: "intel_iris",
      os: "windows",
      touch_screen: 1,
      ips: 0,
      x_res: 1920,
      y_res: 1200,
      ppi: 161,
      dedicated_gpu: 0,
      ram_gb: 16,
      weight_kg: 1.35,
      ssd: 512,
      hhd: 0,
      storage_type: "ssd_only",
      total_storage_gb: 512,
      storage_category: "standard_(512gb-1tb)",
    });
  });
});
