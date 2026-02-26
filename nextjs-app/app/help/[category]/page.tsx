import { loadCategories } from "@/lib/asvs";
import { notFound } from "next/navigation";

interface Props {
  params: { category: string };
}

export default function HelpPage({ params }: Props) {
  const categoryId = parseInt(params.category);
  const categories = loadCategories();
  const category = categories.find((c) => c.id === categoryId);

  if (!category) notFound();

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-2xl font-bold mb-4">{category.title}</h1>

      {category.text && (
        <div
          className="card mb-6 prose dark:prose-invert max-w-none text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ __html: category.text }}
        />
      )}

      {category.urls && category.urls.length > 0 && (
        <div className="card">
          <h2 className="font-semibold mb-3">References</h2>
          <ul className="space-y-2">
            {category.urls.map((link, i) => (
              <li key={i}>
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
                >
                  {link.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6">
        <h2 className="font-semibold mb-3">Other Categories</h2>
        <div className="flex flex-wrap gap-2">
          {categories.map((c) => (
            <a
              key={c.id}
              href={`/help/${c.id}`}
              className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                c.id === categoryId
                  ? "bg-red-600 text-white border-red-600"
                  : "border-gray-300 dark:border-gray-600 hover:border-red-500"
              }`}
            >
              {c.title}
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
