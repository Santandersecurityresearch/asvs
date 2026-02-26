export interface AsvsRequirement {
  chapter_id: string;
  chapter_name: string;
  section_id: string;
  section_name: string;
  req_id: string;
  req_description: string;
  level1: string;
  level2: string;
  level3: string;
  cwe: string;
  nist: string;
  enabled?: number;
  disabled?: number;
  note?: string;
}

export interface AsvsCategory {
  id: number;
  title: string;
  text: string;
  urls?: { title: string; url: string }[];
}

export interface ProjectData {
  project_owner: string;
  project_name: string;
  project_id: number;
  project_description: string;
  project_created: string;
  project_level: number;
  project_allowed_viewers: string;
  requirements: AsvsRequirement[];
}

export interface ProjectRecord {
  id: number;
  projectName: string;
  projectOwner: string;
  projectCreatedAt: Date;
  projectDescription: string;
  projectLevel: number;
  projectAllowedViewers: string;
  dataHash: string;
}

export interface CompletionStats {
  total: number;
  enabled: number;
  percentage: string;
}
