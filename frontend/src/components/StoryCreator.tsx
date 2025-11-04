import React, { useState, useRef } from 'react';
import { X, Upload, FileText, Check, ArrowRight, ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';

interface StoryCreatorProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (storyId: number) => void;
}

interface StepData {
  premise: string;
  genre: string;
  length: string;
  files: File[];
}

export function StoryCreator({ isOpen, onClose, onSuccess }: StoryCreatorProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<StepData>({
    premise: '',
    genre: 'Urban Fantasy',
    length: 'Short',
    files: [],
  });
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  if (!isOpen) return null;

  const totalSteps = 3;

  const handleInputChange = (field: keyof StepData, value: string | File[]) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleFileSelect = (files: FileList | null) => {
    if (files) {
      const fileArray = Array.from(files);
      setFormData(prev => ({ ...prev, files: [...prev.files, ...fileArray] }));
    }
  };

  const handleRemoveFile = (index: number) => {
    setFormData(prev => ({
      ...prev,
      files: prev.files.filter((_, i) => i !== index),
    }));
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  const handleSubmit = async () => {
    if (!formData.premise.trim()) return;

    setLoading(true);
    try {
      const storyData = {
        premise: formData.premise,
        genre: formData.genre,
        length: formData.length,
      };

      // Create story
      const response = await api.post('/stories', storyData);
      const storyId = response.data.id;

      // Upload files if any
      if (formData.files.length > 0) {
        // TODO: Implement file upload
        console.log('Files to upload:', formData.files);
      }

      onSuccess?.(storyId);
      onClose();
      setFormData({ premise: '', genre: 'Urban Fantasy', length: 'Short', files: [] });
      setCurrentStep(1);
    } catch (error) {
      console.error('Failed to create story:', error);
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    if (currentStep === 1) return formData.premise.trim().length > 0;
    if (currentStep === 2) return true;
    return true;
  };

  return (
    <div
      className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-bg-secondary border border-border-default rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden animate-slide-up shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-8 pt-8 pb-4 border-b border-border-subtle">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-text-primary">Create New Story</h2>
            <button
              onClick={onClose}
              className="btn-icon"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Progress Indicator */}
          <div className="flex gap-2">
            {Array.from({ length: totalSteps }).map((_, i) => {
              const stepNum = i + 1;
              const isActive = stepNum === currentStep;
              const isComplete = stepNum < currentStep;

              return (
                <div
                  key={stepNum}
                  className={`flex-1 h-1 rounded-full transition-all ${
                    isComplete
                      ? 'bg-success'
                      : isActive
                      ? 'bg-primary-500'
                      : 'bg-border-subtle'
                  }`}
                />
              );
            })}
          </div>
        </div>

        {/* Body */}
        <div className="p-8 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Step 1: Story Premise */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-semibold text-text-primary mb-2">
                  Step 1 of {totalSteps}: Story Premise
                </h3>
                <p className="text-text-secondary">Tell us your story idea</p>
              </div>

              <div className="form-group">
                <label className="form-label">Story Premise</label>
                <textarea
                  className="form-textarea"
                  placeholder="A shy barista discovers she can pause time for 10 seconds, but each pause steals hours from tomorrow..."
                  value={formData.premise}
                  onChange={(e) => handleInputChange('premise', e.target.value)}
                  rows={4}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="form-group">
                  <label className="form-label">Genre</label>
                  <select
                    className="form-input"
                    value={formData.genre}
                    onChange={(e) => handleInputChange('genre', e.target.value)}
                  >
                    <option value="Urban Fantasy">Urban Fantasy</option>
                    <option value="Sci-Fi">Sci-Fi</option>
                    <option value="Fantasy">Fantasy</option>
                    <option value="Mystery">Mystery</option>
                    <option value="Romance">Romance</option>
                    <option value="Thriller">Thriller</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Length</label>
                  <select
                    className="form-input"
                    value={formData.length}
                    onChange={(e) => handleInputChange('length', e.target.value)}
                  >
                    <option value="Short">Short Story</option>
                    <option value="Novella">Novella</option>
                    <option value="Novel">Novel</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Knowledge Base (Optional) */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-semibold text-text-primary mb-2">
                  Step 2 of {totalSteps}: Knowledge Base
                </h3>
                <p className="text-text-secondary">Upload reference materials (optional)</p>
              </div>

              <div
                className={`file-upload-zone ${dragActive ? 'dragover' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-12 h-12 mx-auto mb-4 text-text-tertiary" />
                <p className="text-text-primary font-medium mb-2">
                  Drag & drop files or click to browse
                </p>
                <p className="text-sm text-text-secondary">
                  Supports .md, .txt, .pdf files
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".md,.txt,.pdf"
                  className="hidden"
                  onChange={(e) => handleFileSelect(e.target.files)}
                />
              </div>

              {formData.files.length > 0 && (
                <div className="space-y-2">
                  <label className="form-label">Uploaded Files</label>
                  <div className="flex flex-wrap gap-2">
                    {formData.files.map((file, index) => (
                      <div
                        key={index}
                        className="inline-flex items-center gap-2 px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-full text-sm text-text-secondary"
                      >
                        <FileText className="w-4 h-4" />
                        <span className="max-w-[200px] truncate">{file.name}</span>
                        <button
                          onClick={() => handleRemoveFile(index)}
                          className="ml-1 text-text-tertiary hover:text-error transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Review */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-semibold text-text-primary mb-2">
                  Step 3 of {totalSteps}: Review
                </h3>
                <p className="text-text-secondary">Review your story details</p>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-bg-tertiary rounded-lg border border-border-subtle">
                  <label className="text-sm text-text-tertiary mb-1 block">Premise</label>
                  <p className="text-text-primary">{formData.premise}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-bg-tertiary rounded-lg border border-border-subtle">
                    <label className="text-sm text-text-tertiary mb-1 block">Genre</label>
                    <p className="text-text-primary">{formData.genre}</p>
                  </div>

                  <div className="p-4 bg-bg-tertiary rounded-lg border border-border-subtle">
                    <label className="text-sm text-text-tertiary mb-1 block">Length</label>
                    <p className="text-text-primary">{formData.length}</p>
                  </div>
                </div>

                {formData.files.length > 0 && (
                  <div className="p-4 bg-bg-tertiary rounded-lg border border-border-subtle">
                    <label className="text-sm text-text-tertiary mb-2 block">
                      Files ({formData.files.length})
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {formData.files.map((file, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-bg-primary rounded text-xs text-text-secondary"
                        >
                          <FileText className="w-3 h-3" />
                          {file.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-8 py-6 border-t border-border-subtle flex items-center justify-between gap-4">
          <button
            onClick={() => currentStep > 1 ? setCurrentStep(currentStep - 1) : onClose()}
            className="btn-secondary"
            disabled={loading}
          >
            {currentStep > 1 ? (
              <>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </>
            ) : (
              'Cancel'
            )}
          </button>

          <button
            onClick={() => {
              if (currentStep < totalSteps) {
                setCurrentStep(currentStep + 1);
              } else {
                handleSubmit();
              }
            }}
            className="btn-primary inline-flex items-center gap-2"
            disabled={!canProceed() || loading}
          >
            {loading ? (
              'Creating...'
            ) : currentStep < totalSteps ? (
              <>
                Continue
                <ArrowRight className="w-4 h-4" />
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Create Story
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
