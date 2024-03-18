import { NextRequest, NextResponse } from "next/server";
import { Message as VercelChatMessage, StreamingTextResponse } from "ai";

import { PromptTemplate } from "@langchain/core/prompts";
import { ChatGoogle } from "@langchain/google-gauth";
import { CustomTransformOutputParser } from "./parser"

const formatMessage = (message: VercelChatMessage) => {
  return `${message.role}: ${message.content}`;
};
const TEMPLATE = `You are a pirate named Patchy. All responses must be extremely verbose and in pirate dialect.

Current conversation:
{chat_history}

User: {input}
AI:`;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const messages = body.messages ?? [];

    // Chat history
    const formattedPreviousMessages = messages.slice(0, -1).map(formatMessage);

    // Current message
    const currentMessageContent = messages[messages.length - 1].content;

    // Prompt template
    const prompt = PromptTemplate.fromTemplate(TEMPLATE);

    // Gemini model
    const model = new ChatGoogle({temperature: 0.7});

    // Extract text (drop other metadata from the response)
    const outputParser = new CustomTransformOutputParser()

    // Construct chain
    const chain = prompt.pipe(model).pipe(outputParser);

    // Run chain
    const stream = await chain.stream({
      chat_history: formattedPreviousMessages.join("\n"),
      input: currentMessageContent,
    });

    return new StreamingTextResponse(stream);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: e.status ?? 500 });
  }
}
