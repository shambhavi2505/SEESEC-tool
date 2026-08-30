
import re


TECH_SIGNATURES = {
    # ------------------------------------------------------------
    # CMS / Site builders
    # ------------------------------------------------------------
    "WordPress":     {"category": "CMS", "patterns": ["wp-content", "wp-includes", "wp-json"]},
    "Shopify":       {"category": "CMS", "patterns": ["cdn.shopify.com", "myshopify.com"]},
    "Webflow":       {"category": "CMS", "patterns": ["webflow.com", "assets-global.website-files.com"]},
    "Wix":           {"category": "CMS", "patterns": ["wix.com", "wixstatic.com"]},
    "Squarespace":   {"category": "CMS", "patterns": ["squarespace.com", "sqsp.net"]},
    "Contentful":    {"category": "CMS", "patterns": ["contentful.com"]},
    "Drupal":        {"category": "CMS", "patterns": ["drupal.js", "sites/default/files"]},
    "HubSpot CMS":   {"category": "CMS", "patterns": ["hs-scripts.com", "hubspot.net", "hsforms"]},

    # ------------------------------------------------------------
    # JS frameworks / rendering
    # ------------------------------------------------------------
    "Next.js":       {"category": "Framework", "patterns": ["/_next/", "__next"]},
    "Nuxt.js":       {"category": "Framework", "patterns": ["/_nuxt/"]},
    "Gatsby":        {"category": "Framework", "patterns": ["gatsby-", "___gatsby"]},
    "React":         {"category": "Framework", "patterns": ["react-dom", "data-reactroot"]},
    "Vue.js":        {"category": "Framework", "patterns": ["vue.js", "vue.min.js", "v-cloak"]},
    "Angular":       {"category": "Framework", "patterns": ["ng-version", "angular.min.js"]},

    # ------------------------------------------------------------
    # Analytics / tracking
    # ------------------------------------------------------------
    "Google Analytics": {"category": "Analytics", "patterns": ["googletagmanager.com", "google-analytics.com", "gtag("]},
    "Hotjar":            {"category": "Analytics", "patterns": ["hotjar.com"]},
    "Segment":            {"category": "Analytics", "patterns": ["cdn.segment.com"]},
    "Mixpanel":           {"category": "Analytics", "patterns": ["mixpanel.com"]},
    "Amplitude":          {"category": "Analytics", "patterns": ["amplitude.com"]},
    "HubSpot Analytics":  {"category": "Analytics", "patterns": ["hs-analytics.net"]},

    # ------------------------------------------------------------
    # Marketing / chat / CRM widgets
    # ------------------------------------------------------------
    "Intercom":      {"category": "Marketing/Support", "patterns": ["widget.intercom.io"]},
    "Drift":         {"category": "Marketing/Support", "patterns": ["js.driftt.com"]},
    "Zendesk":       {"category": "Marketing/Support", "patterns": ["zdassets.com", "zendesk.com"]},
    "Salesforce":    {"category": "Marketing/Support", "patterns": ["salesforce.com", "force.com"]},
    "Marketo":       {"category": "Marketing/Support", "patterns": ["marketo.com", "mktoresp.com"]},
    "Pardot":        {"category": "Marketing/Support", "patterns": ["pardot.com"]},

    # ------------------------------------------------------------
    # Hosting / CDN / infra
    # ------------------------------------------------------------
    "Cloudflare":    {"category": "Hosting/CDN", "patterns": ["cloudflare.com", "cf-ray"]},
    "AWS CloudFront": {"category": "Hosting/CDN", "patterns": ["cloudfront.net"]},
    "Vercel":        {"category": "Hosting/CDN", "patterns": ["vercel.app", "vercel-insights.com"]},
    "Netlify":       {"category": "Hosting/CDN", "patterns": ["netlify.app", "netlify.com"]},
    "Fastly":        {"category": "Hosting/CDN", "patterns": ["fastly.net"]},

    # ------------------------------------------------------------
    # A/B testing / experimentation
    # ------------------------------------------------------------
    "Optimizely":    {"category": "A/B Testing", "patterns": ["optimizely.com"]},
    "VWO":           {"category": "A/B Testing", "patterns": ["visualwebsiteoptimizer.com"]},
}


def detect_tech_stack(html):
   

    if not html:
        return []

    html_lower = html.lower()

    detected = []

    for tech_name, info in TECH_SIGNATURES.items():

        for pattern in info["patterns"]:

            if pattern.lower() in html_lower:

                detected.append({
                    "name": tech_name,
                    "category": info["category"],
                })

                break  # one match per tech is enough

    generator_match = re.search(
        r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )

    if generator_match:

        generator_value = generator_match.group(1).strip()

        already_detected = any(
            d["name"].lower() in generator_value.lower()
            for d in detected
        )

        if generator_value and not already_detected:

            detected.append({
                "name": generator_value,
                "category": "CMS (from generator tag)",
            })

    return detected