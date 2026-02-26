import Link from "next/link";
import Image from "next/image";

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <Image
          src="/img/logoicon.png"
          alt="OWASP Logo"
          width={80}
          height={80}
          className="mx-auto mb-4"
        />
        <h1 className="text-3xl font-bold mb-2">
          OWASP Application Security Verification Standard
        </h1>
        <p className="text-xl text-red-600 font-semibold">Version 5.0</p>
        <p className="mt-4 text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
          A framework of security requirements that defines the security controls required when
          designing, developing and testing modern web applications and web services.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-12">
        {[1, 2, 3].map((level) => (
          <Link
            key={level}
            href={`/levels/${level}`}
            className="card hover:shadow-lg transition-shadow border-l-4 border-red-600 group"
          >
            <h2 className="text-xl font-bold mb-2 group-hover:text-red-600">Level {level}</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {level === 1 && "Opportunistic security — baseline controls against common vulnerabilities."}
              {level === 2 && "Standard application security — most applications should achieve this level."}
              {level === 3 && "Advanced application security — for critical systems requiring high assurance."}
            </p>
          </Link>
        ))}
      </div>

      <div className="text-center">
        <Link href="/projects" className="btn-primary inline-block mr-4">
          Manage Projects
        </Link>
        <Link href="/help/1" className="btn-secondary inline-block">
          View Help
        </Link>
      </div>
    </div>
  );
}
