"""Prompt a model using most relevant samples."""
from flask import Flask, request, make_response
import os
from langchain.document_loaders import RecursiveUrlLoader
from bs4 import BeautifulSoup as Soup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import VertexAI
from langchain import hub
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

# Hack to get correct pysqlite3 version
__import__("pysqlite3")
import sys  # noqa: E402

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")


app = Flask(__name__)

# Global Variables (CHANGE THESE)
PROJECT_ID = "PROJECT-ID"


def load_documents():
    """Load websites from URLs into LangChain documents."""
    url = "https://developers.google.com/machine-learning/guides/"
    loader = RecursiveUrlLoader(
        url=url, max_depth=2, extractor=lambda x: Soup(x, "html.parser").text
    )
    return loader.load()


def split_documents(documents):
    """Split the documents into chunks so we can embed them."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    return text_splitter.split_documents(documents)


def init_retriever(all_splits):
    """We now create a vectorstore so we can retrieve relevant embeddings."""

    from langchain.embeddings import VertexAIEmbeddings
    from langchain.vectorstores import Chroma

    vectorstore = Chroma.from_documents(
        documents=all_splits, embedding=VertexAIEmbeddings()
    )

    return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


documents = load_documents()
splits = split_documents(documents)

RETRIEVER = init_retriever(splits)
LLM = VertexAI(temperature=0)
PROMPT = hub.pull("rlm/rag-prompt")


@app.route("/", methods=["POST"])
def chat():
    """Return a response to a question."""
    user_question = request.json["question"]

    RAG_CHAIN = (
        {"context": RETRIEVER | format_docs, "question": RunnablePassthrough()}
        | PROMPT
        | LLM
        | StrOutputParser()
    )

    output = ""
    for chunk in RAG_CHAIN.stream(user_question):
        output += chunk

    # Send response
    response = make_response(output, 200)
    response.mimetype = "text/plain"
    return response


if __name__ == "__main__":
    print("Launching server...")
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
