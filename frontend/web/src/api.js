const API_BASE_URL = (
  import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"
).replace(/\/$/, "");
export const API_URL = API_BASE_URL.endsWith("/api/v1")
  ? API_BASE_URL
  : `${API_BASE_URL}/api/v1`;

export const RESOLUTIONS = {
  "Full HD (1920x1080)": ["full_hd_(1080p)", 1920, 1080, 141],
  "WUXGA (1920x1200)": ["1920_x_1200", 1920, 1200, 161],
  "QHD+ (2880x1800)": ["2880_x_1800", 2880, 1800, 242],
  "HD (1280x720)": ["hd_(720p,_768p,_900p)", 1280, 720, 126],
};

export function buildPredictionPayload(form) {
  const [screen_resolution, presetX, presetY, presetPpi] =
    RESOLUTIONS[form.resolution];
  return {
    company: form.company,
    type_name: form.type_name,
    inches: Number(form.inches),
    screen_resolution,
    cpu: form.cpu,
    gpu: form.gpu,
    os: form.os,
    touch_screen: Number(form.touch_screen),
    ips: Number(form.ips),
    x_res: Number(form.x_res || presetX),
    y_res: Number(form.y_res || presetY),
    ppi: Number(form.ppi || presetPpi),
    dedicated_gpu: Number(form.dedicated_gpu),
    ram_gb: Number(form.ram_gb),
    weight_kg: Number(form.weight_kg),
    ssd: Number(form.ssd),
    hhd: Number(form.hhd),
    storage_type: form.storage_type,
    total_storage_gb: Number(form.ssd) + Number(form.hhd),
    storage_category: form.storage_category,
  };
}

export async function predictLaptop(form, fetcher = window.fetch) {
  let response;
  try {
    response = await fetcher(`${API_URL}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPredictionPayload(form)),
    });
  } catch {
    throw new Error(
      "Could not connect to the prediction backend. Check that the FastAPI service is running.",
    );
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The backend returned an invalid JSON response.");
  }
  if (!response.ok) {
    throw new Error(
      `Backend request failed (${response.status}): ${data.detail || "Unknown backend error"}`,
    );
  }
  if (!data || typeof data.predicted_price !== "number") {
    throw new Error("The backend returned no prediction.");
  }
  return data;
}
