import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from dotenv import load_dotenv
load_dotenv()


def generate_competitor_summary(company_name, articles):
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    titles = "\n".join([f"- {a['title']}" for a in articles[:50]])
    
    prompt = f"""You are a competitive intelligence analyst.
    
Company being analysed: {company_name}

Their recent content:
{titles}

Answer these 3 things in JSON format:
1. marketing_strategy: What is their content strategy in 2-3 sentences?
2. top_topics: List their top 5 content topics
3. seesec_recommendations: What should SEESEC do to compete? Give 3 specific actions.

Respond ONLY with valid JSON, no explanation."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.3
    )
    
    return response.choices[0].message.content