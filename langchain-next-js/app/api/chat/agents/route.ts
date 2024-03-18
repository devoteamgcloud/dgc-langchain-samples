import { NextRequest, NextResponse } from "next/server";
import { Message as VercelChatMessage, StreamingTextResponse } from "ai";
import { Readable, Transform } from "stream";
import { AIMessage, ChatMessage, HumanMessage } from "@langchain/core/messages";
import { IterableReadableStream } from "@langchain/core/utils/stream";
import { VertexAI, FunctionDeclarationSchemaType } from '@google-cloud/vertexai';

const convertMessageToChatHistory = (message: VercelChatMessage) => {
  return {
    role: message.role,
    parts: [{text: message.content}]
  };
};

const AGENT_SYSTEM_TEMPLATE = `You are a talking parrot named Polly. All final responses must be how a talking parrot would respond. Squawk often!\n`;

const functionDeclarations = [
  {
    function_declarations: [
      {
        name: 'get_word_length',
        description: 'Returns the length of a word.',
        parameters: {
          type: FunctionDeclarationSchemaType.OBJECT,
          properties: {
            text: {type: FunctionDeclarationSchemaType.STRING},
          },
          required: ['text'],
        },
      }
    ],
  },
];

type FunctionParameters = {
  text?: string,
}

function getWordLength(params: FunctionParameters) {
  return params.text!.length
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const messages = (body.messages ?? []).filter(
      (message: VercelChatMessage) =>
        message.role === "user" || message.role === "assistant",
    );

    // Chat history
    const previousMessages = messages
      .slice(0, -1)
      .map(convertMessageToChatHistory);

    // Current message
    const currentMessageContent = messages[messages.length - 1].content;

    // Init Vertex AI
    const vertexAI = new VertexAI({project: "langchain-js-samples", location: "europe-west1"});

    // Instantiate the model
    const generativeModel = vertexAI.getGenerativeModel({
      model: 'gemini-1.0-pro',
    });
  
    // Create a chat session and pass your function declarations
    const chat = generativeModel.startChat({
      history: previousMessages,
      tools: functionDeclarations,
    });

    // This should include a functionCall response from the model
    let result = await chat.sendMessageStream(currentMessageContent);
    console.log((await result.response).candidates[0])
    if ((await result.response).candidates[0].content.parts[0].functionCall) {
      // Construct response
      const params: FunctionParameters = (await result.response).candidates[0].content.parts[0].functionCall?.args!;
      const functionResponseParts = [
        {
          functionResponse: {
            name: "get_word_length",
            response:
                {name: "get_word_length", content: getWordLength(params)},
          },
        }
      ];
    
      // Send a follow up message with a FunctionResponse
      result = await chat.sendMessageStream(functionResponseParts);
    }

    const rs = new ReadableStream({
      async start(controller) {
        for (const item of (await result.response).candidates) {
          controller.enqueue(item.content.parts[0].text);
        }
        controller.close();
      }
    });

    return new StreamingTextResponse(rs);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: e.status ?? 500 });
  }
}
