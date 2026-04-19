import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { AnalysisResponse, EstimateApiResponse } from '@/services/api';

export type BarcodeResult = {
  type: string;
  value: string;
};

type ScanImagesContextValue = {
  images: string[];
  setImages: React.Dispatch<React.SetStateAction<string[]>>;
  clearImages: () => void;
  barcode: BarcodeResult | null;
  setBarcode: (b: BarcodeResult | null) => void;
  analysisResult: AnalysisResponse | null;
  setAnalysisResult: (r: AnalysisResponse | null) => void;
  estimateResult: EstimateApiResponse | null;
  setEstimateResult: (r: EstimateApiResponse | null) => void;
  /** Clears images, barcode, analysis, and pricing estimate (full reset for a new scan). */
  resetScanSession: () => void;
};

const ScanImagesContext = createContext<ScanImagesContextValue | null>(null);

export function ScanImagesProvider({ children }: { children: React.ReactNode }) {
  const [images, setImages] = useState<string[]>([]);
  const [barcode, setBarcodeState] = useState<BarcodeResult | null>(null);
  const [analysisResult, setAnalysisResultState] = useState<AnalysisResponse | null>(null);
  const [estimateResult, setEstimateResultState] = useState<EstimateApiResponse | null>(null);

  const clearImages = useCallback(() => setImages([]), []);
  const setBarcode = useCallback((b: BarcodeResult | null) => setBarcodeState(b), []);
  const setAnalysisResult = useCallback((r: AnalysisResponse | null) => setAnalysisResultState(r), []);
  const setEstimateResult = useCallback((r: EstimateApiResponse | null) => setEstimateResultState(r), []);

  const resetScanSession = useCallback(() => {
    setImages([]);
    setBarcodeState(null);
    setAnalysisResultState(null);
    setEstimateResultState(null);
  }, []);

  const value = useMemo(
    () => ({
      images,
      setImages,
      clearImages,
      barcode,
      setBarcode,
      analysisResult,
      setAnalysisResult,
      estimateResult,
      setEstimateResult,
      resetScanSession,
    }),
    [images, clearImages, barcode, setBarcode, analysisResult, setAnalysisResult, estimateResult, setEstimateResult, resetScanSession]
  );

  return <ScanImagesContext.Provider value={value}>{children}</ScanImagesContext.Provider>;
}

export function useScanImages() {
  const ctx = useContext(ScanImagesContext);
  if (!ctx) throw new Error('useScanImages must be used within ScanImagesProvider');
  return ctx;
}
