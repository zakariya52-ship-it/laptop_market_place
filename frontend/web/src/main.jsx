import { useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  Check,
  ChevronDown,
  Cpu,
  Database,
  Laptop,
  Menu,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import "./styles.css";
import { predictLaptop, RESOLUTIONS } from "./api";
import laptopAsset from "./assets/StockCake-Modern_Laptop_Technology-3721107-standard.png";
import {
  COMPANIES,
  CPUS,
  GPUS,
  OPERATING_SYSTEMS,
  STORAGE_CATEGORIES,
  STORAGE_TYPES,
  TYPE_NAMES,
} from "./knownValues";

const initialForm = {
  company: "lenovo",
  type_name: "lenovo_thinkpad_t14_gen_5",
  inches: 14,
  resolution: "WUXGA (1920x1200)",
  cpu: "intel_core_i7-1165g7",
  gpu: "intel_iris_xe_graphics_g7_(96eu)",
  os: "windows",
  touch_screen: 0,
  ips: 0,
  dedicated_gpu: 0,
  ram_gb: 16,
  weight_kg: 1.35,
  x_res: 1920,
  y_res: 1200,
  ppi: 161,
  ssd: 512,
  hhd: 0,
  storage_type: "ssd_only",
  storage_category: "standard_(512gb-1tb)",
};

function App() {
  const [page, setPage] = useState("home");
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);

  const navigate = (nextPage) => {
    setPage(nextPage);
    setMobileNav(false);
    setError("");
  };
  const update = (event) =>
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      setResult(await predictLaptop(form));
      setPage("result");
    } catch (submissionError) {
      setError(submissionError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => navigate("home")} aria-label="Go home">
          <span className="brand-mark"><Laptop size={19} /></span>
          <span>Laptop Price Lab</span>
        </button>
        <button className="mobile-menu" onClick={() => setMobileNav(!mobileNav)} aria-label="Toggle navigation">
          {mobileNav ? <X size={21} /> : <Menu size={21} />}
        </button>
        <nav className={mobileNav ? "nav-links open" : "nav-links"}>
          {[
            ["home", "Home"],
            ["engine", "Valuation Engine"],
            ["marketplace", "Buy / Marketplace"],
            ["rentals", "Rentals"],
          ].map(([key, label]) => (
            <button className={page === key ? "nav-link active" : "nav-link"} key={key} onClick={() => navigate(key)}>
              {label}
            </button>
          ))}
          <button className="nav-cta" onClick={() => navigate("engine")}>Get an estimate <ArrowRight size={16} /></button>
        </nav>
      </header>

      <main>
        {page === "home" && <Home navigate={navigate} />}
        {page === "engine" && (
          <Engine form={form} update={update} submit={submit} loading={loading} error={error} navigate={navigate} />
        )}
        {page === "result" && <Result result={result} navigate={navigate} />}
        {(page === "marketplace" || page === "rentals") && <Placeholder page={page} navigate={navigate} />}
      </main>
      <footer><span>© {new Date().getFullYear()} Laptop Price Lab</span><span>Data-driven estimates, made clear.</span></footer>
    </div>
  );
}

function Home({ navigate }) {
  return (
    <>
      <section className="hero section">
        <div className="hero-copy">
          <p className="eyebrow">Laptop valuation, made simple</p>
          <h1>Find Your Laptop&apos;s Market Value</h1>
          <p className="hero-description">
            Turn your laptop&apos;s specifications into a fast, data-driven estimate.
            A clear starting point for selling, buying, or simply knowing what you own.
          </p>
          <button className="primary-button hero-button" onClick={() => navigate("engine")}>
            Estimate Laptop Value <ArrowRight size={18} />
          </button>
          <div className="trust-row"><ShieldCheck size={17} /><span>Powered by the existing Laptop Price Lab prediction service</span></div>
        </div>
        <div className="hero-visual">
          <img className="hero-image" src={laptopAsset} alt="Modern laptop technology" />
        </div>
      </section>
      <section className="section feature-section">
        <div className="section-heading"><p className="eyebrow">A better way to price hardware</p><h2>Simple inputs. Useful answers.</h2></div>
        <div className="feature-grid">
          <Feature icon={<Cpu />} title="Configure precisely" text="Capture processor, graphics, display, memory, weight, and storage details." />
          <Feature icon={<Sparkles />} title="Estimate instantly" text="Submit directly to the FastAPI prediction service without duplicating model logic." />
          <Feature icon={<Database />} title="Make a confident move" text="Use a clear market estimate as a practical reference for your next decision." />
        </div>
      </section>
    </>
  );
}

function Feature({ icon, title, text }) {
  return <article className="feature-card"><div className="icon-box">{icon}</div><h3>{title}</h3><p>{text}</p></article>;
}

function Engine({ form, update, submit, loading, error, navigate }) {
  return (
    <section className="section engine-page">
      <div className="page-heading"><div><p className="eyebrow">Valuation engine</p><h2>Configure your laptop</h2><p>Give us the details you know. We&apos;ll take care of the estimate.</p></div><button className="quiet-button" onClick={() => navigate("home")}>Back home</button></div>
      <form className="config-card" onSubmit={submit}>
        <fieldset><legend><span className="legend-number">01</span> Core specifications</legend><div className="field-grid">
          <Autocomplete label="Company" name="company" value={form.company} options={COMPANIES} onChange={update} />
          <Autocomplete label="Operating system" name="os" value={form.os} options={OPERATING_SYSTEMS} onChange={update} />
          <Autocomplete label="Model / TypeName" name="type_name" value={form.type_name} options={TYPE_NAMES} onChange={update} />
          <Autocomplete label="Processor" name="cpu" value={form.cpu} options={CPUS} onChange={update} />
          <Autocomplete label="Graphics" name="gpu" value={form.gpu} options={GPUS} onChange={update} />
          <Field label="Screen size (inches)" type="number" min="10" max="20" step="0.1" name="inches" value={form.inches} onChange={update} required />
          <Field label="Memory (GB)" type="number" min="2" max="128" name="ram_gb" value={form.ram_gb} onChange={update} required />
          <Field label="Weight (kg)" type="number" min="0.8" max="4" step="0.01" name="weight_kg" value={form.weight_kg} onChange={update} required />
        </div></fieldset>
        <fieldset><legend><span className="legend-number">02</span> Display & features</legend><div className="field-grid">
          <Autocomplete label="Screen resolution" name="resolution" value={form.resolution} options={Object.keys(RESOLUTIONS)} onChange={update} />
          <Field label="X resolution" type="number" min="800" max="4000" name="x_res" value={form.x_res} onChange={update} required />
          <Field label="Y resolution" type="number" min="600" max="3000" name="y_res" value={form.y_res} onChange={update} required />
          <Field label="PPI" type="number" min="80" max="300" step="0.1" name="ppi" value={form.ppi} onChange={update} required />
          <Toggle label="Touch screen" name="touch_screen" value={form.touch_screen} onChange={update} />
          <Toggle label="IPS display" name="ips" value={form.ips} onChange={update} />
          <Toggle label="Dedicated GPU" name="dedicated_gpu" value={form.dedicated_gpu} onChange={update} />
        </div></fieldset>
        <fieldset><legend><span className="legend-number">03</span> Storage profile</legend><div className="field-grid">
          <Autocomplete label="Storage type" name="storage_type" value={form.storage_type} options={STORAGE_TYPES} onChange={update} />
          <Autocomplete label="Storage category" name="storage_category" value={form.storage_category} options={STORAGE_CATEGORIES} onChange={update} />
          <Field label="SSD (GB)" type="number" min="0" max="8000" step="128" name="ssd" value={form.ssd} onChange={update} required />
          <Field label="HHD (GB)" type="number" min="0" max="4000" step="128" name="hhd" value={form.hhd} onChange={update} required />
        </div></fieldset>
        {error && <div className="error-banner" role="alert">{error}</div>}
        <div className="form-actions"><span><Check size={16} /> Your details stay in this browser</span><button className="primary-button" type="submit" disabled={loading}>{loading ? "Calculating..." : "Estimate Laptop Value"} <ArrowRight size={18} /></button></div>
      </form>
    </section>
  );
}

function Field({ label, children, ...props }) {
  return <label className="field"><span>{label}</span>{children || <input {...props} />}</label>;
}

function Autocomplete({ label, name, value, options, onChange }) {
  const [query, setQuery] = useState(value);
  const [open, setOpen] = useState(false);
  const matches = options
    .filter((option) => option.toLowerCase().includes(query.trim().toLowerCase()))
    .slice(0, 80);

  const selectOption = (option) => {
    setQuery(option);
    setOpen(false);
    onChange({ target: { name, value: option } });
  };

  return (
    <label className="field autocomplete-field">
      <span>{label}</span>
      <div className={open ? "autocomplete open" : "autocomplete"}>
        <input
          aria-autocomplete="list"
          aria-expanded={open}
          aria-label={label}
          autoComplete="off"
          name={name}
          onBlur={() => {
            window.setTimeout(() => {
              setQuery(value);
              setOpen(false);
            }, 120);
          }}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          role="combobox"
          value={query}
        />
        {open && (
          <div className="autocomplete-menu" role="listbox">
            {matches.length > 0 ? (
              matches.map((option) => (
                <button
                  className={option === value ? "autocomplete-option selected" : "autocomplete-option"}
                  key={option}
                  onMouseDown={(event) => {
                    event.preventDefault();
                    selectOption(option);
                  }}
                  role="option"
                  type="button"
                >
                  {option}
                </button>
              ))
            ) : (
              <div className="autocomplete-empty">No approved matches</div>
            )}
            {options.length > matches.length && (
              <div className="autocomplete-count">
                Showing {matches.length} of {options.length} approved options
              </div>
            )}
          </div>
        )}
      </div>
    </label>
  );
}

function Toggle({ label, name, value, onChange }) {
  return <label className="toggle-field"><span>{label}</span><select name={name} value={value} onChange={onChange}><option value="0">No</option><option value="1">Yes</option></select><ChevronDown size={15} /></label>;
}

function Result({ result, navigate }) {
  if (!result) return <Placeholder page="engine" navigate={navigate} />;
  return <section className="section result-page"><button className="quiet-button" onClick={() => navigate("engine")}>← Edit specifications</button><div className="result-card"><div className="success-icon"><Check size={22} /></div><p className="eyebrow">Your laptop valuation</p><p className="result-label">Estimated market value</p><div className="result-price">{result.predicted_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} <small>{result.currency || "USD"}</small></div><div className="celebration"><Sparkles size={18} /><span>Congratulations! You got your price in milliseconds</span></div><p className="result-helper">A data-driven estimate based on the specifications you provided.</p><button className="primary-button" onClick={() => navigate("engine")}>Estimate another laptop <ArrowRight size={18} /></button></div></section>;
}

function Placeholder({ page, navigate }) {
  const title = page === "marketplace" ? "Buy / Marketplace" : page === "rentals" ? "Rentals" : "Valuation Engine";
  return <section className="section placeholder-page"><div className="placeholder-card"><div className="icon-box"><Laptop /></div><p className="eyebrow">Coming soon</p><h2>{title}</h2><p>This area is not connected to listings or rental inventory yet. Use the Valuation Engine for the available prediction workflow.</p><button className="primary-button" onClick={() => navigate("engine")}>Open Valuation Engine <ArrowRight size={18} /></button></div></section>;
}

createRoot(document.getElementById("root")).render(<App />);
