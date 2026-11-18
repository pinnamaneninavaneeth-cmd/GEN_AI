import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file():
    """Load simple KEY=VALUE settings from the .env file without extra packages."""
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass
class FeatureBudget:
    requests_per_day: int
    avg_input_tokens: int
    avg_output_tokens: int
    peak_requests_per_minute: int
    input_price_per_million: float
    output_price_per_million: float
    rpm_limit: int
    tpm_limit: int
    monthly_budget_usd: float
    daily_budget_usd: float
    safety_margin_percent: float

    @classmethod
    def from_env(cls):
        load_env_file()
        return cls(
            requests_per_day=int(os.getenv("REQUESTS_PER_DAY", "2000")),
            avg_input_tokens=int(os.getenv("AVG_INPUT_TOKENS", "1200")),
            avg_output_tokens=int(os.getenv("AVG_OUTPUT_TOKENS", "300")),
            peak_requests_per_minute=int(os.getenv("PEAK_REQUESTS_PER_MINUTE", "30")),
            input_price_per_million=float(os.getenv("INPUT_PRICE_PER_MILLION", "0.30")),
            output_price_per_million=float(os.getenv("OUTPUT_PRICE_PER_MILLION", "1.20")),
            rpm_limit=int(os.getenv("RPM_LIMIT", "60")),
            tpm_limit=int(os.getenv("TPM_LIMIT", "100000")),
            monthly_budget_usd=float(os.getenv("MONTHLY_BUDGET_USD", "50")),
            daily_budget_usd=float(os.getenv("DAILY_BUDGET_USD", "2")),
            safety_margin_percent=float(os.getenv("SAFETY_MARGIN_PERCENT", "20")),
        )

    def calculate(self):
        numeric_values = [
            self.requests_per_day, self.avg_input_tokens,
            self.avg_output_tokens, self.peak_requests_per_minute,
            self.input_price_per_million, self.output_price_per_million,
            self.rpm_limit, self.tpm_limit, self.monthly_budget_usd,
            self.daily_budget_usd, self.safety_margin_percent,
        ]
        if any(value < 0 for value in numeric_values):
            raise ValueError("Budget assumptions and limits cannot be negative.")

        input_day = self.requests_per_day * self.avg_input_tokens
        output_day = self.requests_per_day * self.avg_output_tokens
        daily_cost = (
            input_day * self.input_price_per_million
            + output_day * self.output_price_per_million
        ) / 1_000_000
        monthly_cost = daily_cost * 30
        margin = 1 + self.safety_margin_percent / 100

        peak_rpm = self.peak_requests_per_minute * margin
        peak_tpm = (
            self.peak_requests_per_minute
            * (self.avg_input_tokens + self.avg_output_tokens)
            * margin
        )

        return {
            "input_tokens_day": input_day,
            "output_tokens_day": output_day,
            "total_tokens_day": input_day + output_day,
            "daily_cost_usd": daily_cost,
            "monthly_cost_usd": monthly_cost,
            "peak_rpm_with_margin": peak_rpm,
            "peak_tpm_with_margin": peak_tpm,
            "rpm_ok": peak_rpm <= self.rpm_limit,
            "tpm_ok": peak_tpm <= self.tpm_limit,
            "daily_budget_ok": daily_cost * margin <= self.daily_budget_usd,
            "monthly_budget_ok": monthly_cost * margin <= self.monthly_budget_usd,
        }


def main():
    result = FeatureBudget.from_env().calculate()

    print("=" * 48)
    print("             TOKEN ECONOMICS REPORT")
    print("             Student: Tejaswini")
    print("=" * 48)
    print(f"Input tokens/day:                 {result['input_tokens_day']:,.0f}")
    print(f"Output tokens/day:                {result['output_tokens_day']:,.0f}")
    print(f"Total tokens/day:                 {result['total_tokens_day']:,.0f}")
    print(f"Estimated daily cost:             ${result['daily_cost_usd']:.4f}")
    print(f"Estimated monthly cost (30 days): ${result['monthly_cost_usd']:.2f}")
    print(f"Peak RPM with 20% margin:         {result['peak_rpm_with_margin']:.1f}")
    print(f"Peak total TPM with 20% margin:   {result['peak_tpm_with_margin']:,.0f}")

    checks = {
        "RPM capacity": result["rpm_ok"],
        "TPM capacity": result["tpm_ok"],
        "Daily budget": result["daily_budget_ok"],
        "Monthly budget": result["monthly_budget_ok"],
    }

    print("\nCHECKS")
    for name, passed in checks.items():
        print(f"{name:<20}: {'PASS' if passed else 'REVIEW'}")

    if all(checks.values()):
        print("\nRecommendation: WITHIN configured planning limits.")
    else:
        print("\nRecommendation: REVISE assumptions, limits, or design before build.")
    print("=" * 48)


if __name__ == "__main__":
    main()
