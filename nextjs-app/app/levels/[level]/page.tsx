import { loadRequirementsByLevel } from "@/lib/asvs";
import { notFound } from "next/navigation";
import { AsvsRequirement } from "@/types";

interface Props {
  params: { level: string };
}

const CHAPTER_COLORS: Record<string, string> = {
  "Architecture": "bg-orange-100 dark:bg-orange-900",
  "Authentication": "bg-teal-100 dark:bg-teal-900",
  "Session": "bg-blue-100 dark:bg-blue-900",
  "Access": "bg-yellow-100 dark:bg-yellow-900",
  "Validation": "bg-green-100 dark:bg-green-900",
  "Cryptography": "bg-emerald-100 dark:bg-emerald-900",
  "Stored Cryptography": "bg-emerald-100 dark:bg-emerald-900",
  "Error": "bg-red-100 dark:bg-red-900",
  "Data": "bg-purple-100 dark:bg-purple-900",
  "Communications": "bg-slate-200 dark:bg-slate-700",
  "Malicious": "bg-lime-100 dark:bg-lime-900",
  "Business Logic": "bg-orange-200 dark:bg-orange-800",
  "Files": "bg-cyan-100 dark:bg-cyan-900",
  "API": "bg-green-200 dark:bg-green-800",
  "Configuration": "bg-red-600 text-white",
  "Encoding": "bg-indigo-100 dark:bg-indigo-900",
};

function getChapterColor(chapterName: string): string {
  for (const [key, cls] of Object.entries(CHAPTER_COLORS)) {
    if (chapterName.startsWith(key)) return cls;
  }
  return "bg-gray-100 dark:bg-gray-700";
}

function groupByChapter(requirements: AsvsRequirement[]) {
  const groups: Record<string, { chapterName: string; sections: Record<string, AsvsRequirement[]> }> = {};
  for (const r of requirements) {
    if (!groups[r.chapter_id]) {
      groups[r.chapter_id] = { chapterName: r.chapter_name, sections: {} };
    }
    if (!groups[r.chapter_id].sections[r.section_id]) {
      groups[r.chapter_id].sections[r.section_id] = [];
    }
    groups[r.chapter_id].sections[r.section_id].push(r);
  }
  return groups;
}

export default function LevelPage({ params }: Props) {
  const level = parseInt(params.level);
  if (![1, 2, 3].includes(level)) notFound();

  const requirements = loadRequirementsByLevel(level);
  const groups = groupByChapter(requirements);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">ASVS Level {level}</h1>
      <p className="text-gray-500 dark:text-gray-400 mb-6">{requirements.length} requirements</p>

      <div className="space-y-8">
        {Object.entries(groups).map(([chapterId, { chapterName, sections }]) => (
          <div key={chapterId} className="card">
            <h2 className={`text-lg font-bold px-3 py-2 rounded mb-4 ${getChapterColor(chapterName)}`}>
              {chapterId}: {chapterName}
            </h2>
            {Object.entries(sections).map(([sectionId, reqs]) => (
              <div key={sectionId} className="mb-4">
                <h3 className="font-semibold text-sm text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
                  {sectionId}: {reqs[0].section_name}
                </h3>
                <div className="space-y-2">
                  {reqs.map((r) => (
                    <div key={r.req_id} className="border-l-2 border-gray-200 dark:border-gray-600 pl-3 py-1">
                      <div className="flex gap-2 items-start">
                        <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded shrink-0 mt-0.5">
                          {r.req_id}
                        </span>
                        <p className="text-sm">{r.req_description}</p>
                      </div>
                      <div className="flex gap-2 mt-1 ml-10 text-xs text-gray-400">
                        {r.cwe && <span>CWE: {r.cwe}</span>}
                        {r.nist && <span>NIST: {r.nist}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
