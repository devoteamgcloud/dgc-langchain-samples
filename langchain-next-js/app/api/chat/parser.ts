import { BaseTransformOutputParser } from "@langchain/core/output_parsers";

export class CustomTransformOutputParser extends BaseTransformOutputParser<string> {
    lc_namespace = ["langchain", "output_parsers"];
  
    async parse(text: string): Promise<string> {
      if (text) {
        return JSON.parse(text)[0].text;
      }
      return text
    }
  
    getFormatInstructions(): string {
      return "";
    }
}