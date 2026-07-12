import Navbar from "@/components/Navbar";

const TIERS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "One bucket, manual scans, full analysis.",
    features: ["1 connected bucket", "Unlimited manual scans", "Full waste breakdown"],
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For teams actively managing cloud spend.",
    features: [
      "Up to 10 connected buckets",
      "Scheduled daily scans",
      "One-click optimization execution",
      "Savings history & trends",
    ],
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "Multi-account, SSO, dedicated support.",
    features: ["Unlimited buckets", "SSO / SAML", "Priority support", "Custom retention rules"],
  },
];

export default function PricingPage() {
  return (
    <main>
      <Navbar />
      <div className="px-6 md:px-12 pt-16 pb-24 max-w-5xl">
        <h1 className="font-display font-bold text-3xl mb-2">Pricing</h1>
        <p className="text-muted mb-12">
          Start free. Upgrade once OptiVault is finding real savings.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`rounded-lg p-6 border ${
                tier.highlighted ? "border-savings bg-panel-hover" : "border-border bg-panel"
              }`}
            >
              <p className="font-display font-bold text-lg mb-1">{tier.name}</p>
              <p className="text-muted text-sm mb-6">{tier.description}</p>
              <p className="mb-6">
                <span className="ledger-figure text-3xl">{tier.price}</span>
                <span className="text-muted text-sm">{tier.period}</span>
              </p>
              <ul className="flex flex-col gap-2 mb-8">
                {tier.features.map((f) => (
                  <li key={f} className="text-sm text-muted flex gap-2">
                    <span className="text-savings">—</span> {f}
                  </li>
                ))}
              </ul>
              <button
                disabled={tier.name !== "Free"}
                className={`w-full py-2.5 rounded-md font-medium transition-opacity ${
                  tier.highlighted
                    ? "bg-savings text-ink hover:opacity-90"
                    : "border border-border hover:bg-panel-hover"
                } disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                {tier.name === "Free" ? "Get started" : "Checkout coming soon"}
              </button>
            </div>
          ))}
        </div>

        {/*
          Razorpay checkout wiring intentionally isn't live yet -- it needs
          a Razorpay test-mode key (free, no KYC, ~5 min signup) before
          there's anything real to test against. Once that exists, this
          becomes: POST /payments/create-order on the backend, then
          window.Razorpay(options).open() here using the returned order_id.
        */}
      </div>
    </main>
  );
}
