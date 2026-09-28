from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain.output_parsers import OutputFixingParser

from .models import EmailTriage
from .prompts import build_prompt


def build_llm(api_key: str, model: str, temperature: float = 0.0) -> BaseChatModel:
    from langchain_groq import ChatGroq

    return ChatGroq(api_key=api_key, model=model, temperature=temperature)


def build_triage_chain(llm: BaseChatModel, use_fixing_parser: bool = True) -> Runnable:
    parser = PydanticOutputParser(pydantic_object=EmailTriage)

    final_parser = (
        OutputFixingParser.from_llm(parser=parser, llm=llm)
        if use_fixing_parser
        else parser
    )

    prompt = build_prompt().partial(
        format_instructions=parser.get_format_instructions()
    )

    chain = RunnablePassthrough() | prompt | llm | final_parser
    return chain


def triage_email(chain: Runnable, email_text: str) -> EmailTriage:
    return chain.invoke({"email": email_text})
