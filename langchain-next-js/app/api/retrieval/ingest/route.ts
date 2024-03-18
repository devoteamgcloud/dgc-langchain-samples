import { NextRequest, NextResponse } from "next/server";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

import { Chroma } from "@langchain/community/vectorstores/chroma";
import { GoogleVertexAIEmbeddings } from "@langchain/community/embeddings/googlevertexai";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const text = body.text;

  try {
    // Initialize splitter
    const splitter = RecursiveCharacterTextSplitter.fromLanguage("markdown", {
      chunkSize: 256,
      chunkOverlap: 20,
    });

    // Split text into chunks
    const splitDocuments = await splitter.createDocuments([text]);

    // Initialize Chroma from documents
    await Chroma.fromDocuments(
      splitDocuments,
      new GoogleVertexAIEmbeddings(),
      {collectionName: "collection"},
    )

    return NextResponse.json({ ok: true }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
