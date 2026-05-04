export interface Evidence {
  id: number;
  incident: number;
  image_frame: string | null;
  video_snippet: string | null;
  timestamp: number;
  created_at: string;
}
