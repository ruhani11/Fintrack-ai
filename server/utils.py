import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def format_amount(amount):
    return f"₹{float(amount):,.2f}"


def clean_text(text):
    return " ".join(str(text).split()).strip()


def is_bad_ai_output(text):
    if not text:
        return True

    bad_phrases = [
        "that's straightforward",
        "we need to",
        "the user provided",
        "i need to",
        "let's craft",
        "from the spending",
        "make sure",
        "first, the user",
        "i should",
        "let me",
        "analysis",
        "reasoning",
        "output rules",
        "final answer requirements",
        "do not",
        "start directly",
        "suggested extra savings or investment target is",
        "the second tip should",
        "third tip needs",
        "looking at the data"
    ]

    text_lower = text.lower()
    return any(phrase in text_lower for phrase in bad_phrases)


def format_tips_line_by_line(tips):
    final_tips = []

    for tip in tips:
        tip = clean_text(tip)
        tip = re.sub(r"^\d+\.\s*", "", tip).strip()

        if tip and not is_bad_ai_output(tip):
            final_tips.append(tip)

    if not final_tips:
        return None

    final_tips = final_tips[:3]

    return "\n".join(
        f"{index}. {tip}"
        for index, tip in enumerate(final_tips, start=1)
    )


def extract_ai_content(response):
    try:
        message = response.choices[0].message
        content = getattr(message, "content", None)

        if isinstance(content, list):
            content = " ".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )

        if not isinstance(content, str):
            return None

        text = content.strip()

        if not text:
            return None

        text = text.replace("<tips>", "").replace("</tips>", "").strip()

        markers = [
            "Final tips:",
            "Budgeting tips:",
            "Tips:",
            "Answer:",
            "Final answer:"
        ]

        lower_text = text.lower()

        for marker in markers:
            marker_lower = marker.lower()
            if marker_lower in lower_text:
                index = lower_text.rfind(marker_lower)
                text = text[index + len(marker):].strip()
                break

        first_numbered_tip = re.search(r"\b1\.\s+", text)

        if first_numbered_tip:
            text = text[first_numbered_tip.start():].strip()

        numbered_tips = re.findall(
            r"\d+\.\s+.*?(?=\s+\d+\.|$)",
            text,
            flags=re.DOTALL
        )

        if numbered_tips:
            return format_tips_line_by_line(numbered_tips)

        bullet_tips = re.findall(
            r"(?:^|\n)\s*[-•]\s+(.+)",
            text
        )

        if bullet_tips:
            return format_tips_line_by_line(bullet_tips)

        sentences = re.split(r"(?<=[.!?])\s+", text)
        return format_tips_line_by_line(sentences)

    except Exception:
        return None


def generate_default_tips(
    highest_category,
    suggested_reduction,
    suggested_extra_savings,
    current_savings,
    total_expense,
    income
):
    tips = []

    tips.append(
        f"Reduce {highest_category} by {format_amount(suggested_reduction)} and set a fixed monthly limit for this category."
    )

    if suggested_extra_savings > 0:
        tips.append(
            f"Increase savings/investments by {format_amount(suggested_extra_savings)} this month from your current savings of {format_amount(current_savings)}."
        )
    else:
        tips.append(
            f"Maintain your strong savings of {format_amount(current_savings)} and move a fixed part into investments."
        )

    tips.append(
        f"Keep total expenses near {format_amount(total_expense)} and review spending weekly to protect your income of {format_amount(income)}."
    )

    return "\n".join(
        f"{index}. {tip}"
        for index, tip in enumerate(tips, start=1)
    )


def generate_budget_tip(summary, income):
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            return "AI tip could not be generated because OpenRouter API key is missing."

        income = float(income)

        if income <= 0:
            return "AI tip could not be generated because income must be greater than 0."

        if not summary:
            return "AI tip could not be generated because no expense data was provided."

        total_expense = 0
        breakdown = []

        for category, amount in summary.items():
            amount = float(amount)
            total_expense += amount
            percent = (amount / income) * 100

            breakdown.append(
                f"{category}: {format_amount(amount)} ({percent:.1f}% of income)"
            )

        breakdown_str = "\n".join(breakdown)

        current_savings = income - total_expense
        current_savings_percent = (current_savings / income) * 100

        highest_category = max(
            summary,
            key=lambda category: float(summary[category])
        )

        highest_amount = float(summary[highest_category])
        highest_percent = (highest_amount / income) * 100

        suggested_reduction = highest_amount * 0.20

        if current_savings_percent < 20:
            suggested_extra_savings = (income * 0.20) - current_savings
        else:
            suggested_extra_savings = income * 0.05

        suggested_extra_savings = max(suggested_extra_savings, 0)

        default_tips = generate_default_tips(
            highest_category=highest_category,
            suggested_reduction=suggested_reduction,
            suggested_extra_savings=suggested_extra_savings,
            current_savings=current_savings,
            total_expense=total_expense,
            income=income
        )

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        prompt = f"""
Rewrite the following budgeting tips in simple, polished language.

Important:
Return only the final 3 numbered tips.
Do not include reasoning.
Do not include explanation.
Do not include headings.
Do not change the rupee amounts.
Do not mention subscriptions.

Monthly data:
Income: {format_amount(income)}
Total expenses: {format_amount(total_expense)}
Current savings: {format_amount(current_savings)}
Highest category: {highest_category}
Highest category amount: {format_amount(highest_amount)}
Highest category percentage: {highest_percent:.1f}%

Category-wise expenses:
{breakdown_str}

Draft tips to rewrite:
{default_tips}
"""

        model_name = os.getenv("OPENROUTER_MODEL", "openrouter/free")

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Return only 3 final numbered budgeting tips. "
                            "No reasoning. No analysis. No headings."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=150
            )

            ai_tip = extract_ai_content(response)

            if ai_tip and not is_bad_ai_output(ai_tip):
                return ai_tip

            return default_tips

        except Exception as e:
            error_text = str(e)

            if "429" in error_text or "rate-limited" in error_text:
                return "AI service is temporarily busy because the free model is rate-limited. Please try again after 30 seconds."

            if "404" in error_text or "No endpoints found" in error_text:
                return "Selected AI model is unavailable. Please change OPENROUTER_MODEL in server/.env."

            return default_tips

    except Exception as e:
        return f"AI tip could not be generated: {str(e)}"