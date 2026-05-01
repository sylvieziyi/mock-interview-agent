import { notFound } from "next/navigation";
import { questionById } from "@/lib/questions";
import InterviewClient from "./InterviewClient";

export default async function InterviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const question = questionById(id);
  if (!question) notFound();
  return <InterviewClient question={question} />;
}
