import { create } from "zustand";

interface PlaybackState {
  activeCameraId: string | null;
  currentTime: Date;
  isPlaying: boolean;
  speed: number;
  setCamera: (id: string | null) => void;
  setTime: (time: Date) => void;
  setPlaying: (playing: boolean) => void;
  setSpeed: (speed: number) => void;
}

export const usePlaybackStore = create<PlaybackState>((set) => ({
  activeCameraId: null,
  currentTime: new Date(),
  isPlaying: false,
  speed: 1,

  setCamera: (id) => set({ activeCameraId: id }),
  setTime: (time) => set({ currentTime: time }),
  setPlaying: (playing) => set({ isPlaying: playing }),
  setSpeed: (speed) => set({ speed }),
}));