import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, X, Image, Video, FileText, Check } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface EvidenceFile {
  id: string;
  file: File;
  preview?: string;
  type: 'image' | 'video' | 'document';
  uploaded: boolean;
}

interface EvidenceUploaderProps {
  onFilesChange: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
}

const EvidenceUploader: React.FC<EvidenceUploaderProps> = ({
  onFilesChange,
  maxFiles = 10,
  acceptedTypes = ['image/*', 'video/*', '.pdf', '.doc', '.docx']
}) => {
  const [files, setFiles] = useState<EvidenceFile[]>([]);
  const [dragActive, setDragActive] = useState(false);

  const getFileType = (file: File): 'image' | 'video' | 'document' => {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('video/')) return 'video';
    return 'document';
  };

  const createPreview = (file: File): Promise<string | undefined> => {
    return new Promise((resolve) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.readAsDataURL(file);
      } else {
        resolve(undefined);
      }
    });
  };

  const handleFiles = useCallback(async (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    const remainingSlots = maxFiles - files.length;
    const filesToAdd = fileArray.slice(0, remainingSlots);

    const evidenceFiles: EvidenceFile[] = await Promise.all(
      filesToAdd.map(async (file) => ({
        id: Math.random().toString(36).substr(2, 9),
        file,
        preview: await createPreview(file),
        type: getFileType(file),
        uploaded: false
      }))
    );

    const updatedFiles = [...files, ...evidenceFiles];
    setFiles(updatedFiles);
    onFilesChange(updatedFiles.map(f => f.file));

    // Simulate upload progress
    evidenceFiles.forEach((evidenceFile, index) => {
      setTimeout(() => {
        setFiles(prev => prev.map(f => 
          f.id === evidenceFile.id ? { ...f, uploaded: true } : f
        ));
      }, (index + 1) * 500);
    });
  }, [files, maxFiles, onFilesChange]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (id: string) => {
    const updatedFiles = files.filter(f => f.id !== id);
    setFiles(updatedFiles);
    onFilesChange(updatedFiles.map(f => f.file));
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'image': return Image;
      case 'video': return Video;
      default: return FileText;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Upload className="h-5 w-5 text-primary-600" />
            <span>Upload Evidence</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Upload Area */}
          <div
            className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200 ${
              dragActive 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              multiple
              accept={acceptedTypes.join(',')}
              onChange={handleFileInput}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            
            <div className="space-y-4">
              <div className="mx-auto w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center">
                <Upload className="h-8 w-8 text-primary-600" />
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Drop files here or click to browse
                </h3>
                <p className="text-gray-600">
                  Upload images, videos, or documents that support your carbon claim
                </p>
              </div>
              
              <div className="flex flex-wrap justify-center gap-2 text-sm text-gray-500">
                <span className="px-3 py-1 bg-gray-100 rounded-full">Images</span>
                <span className="px-3 py-1 bg-gray-100 rounded-full">Videos</span>
                <span className="px-3 py-1 bg-gray-100 rounded-full">Documents</span>
              </div>
              
              <p className="text-xs text-gray-500">
                Maximum {maxFiles} files • Up to 10MB each
              </p>
            </div>
          </div>

          {/* File List */}
          <AnimatePresence>
            {files.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6"
              >
                <h4 className="font-medium text-gray-900 mb-4">
                  Uploaded Files ({files.length}/{maxFiles})
                </h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {files.map((evidenceFile) => {
                    const Icon = getFileIcon(evidenceFile.type);
                    
                    return (
                      <motion.div
                        key={evidenceFile.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className="flex items-center space-x-3 p-4 bg-gray-50 rounded-xl border"
                      >
                        {/* Preview/Icon */}
                        <div className="flex-shrink-0">
                          {evidenceFile.preview ? (
                            <img
                              src={evidenceFile.preview}
                              alt={evidenceFile.file.name}
                              className="w-12 h-12 object-cover rounded-lg"
                            />
                          ) : (
                            <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                              <Icon className="h-6 w-6 text-gray-500" />
                            </div>
                          )}
                        </div>
                        
                        {/* File Info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {evidenceFile.file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(evidenceFile.file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                        
                        {/* Status */}
                        <div className="flex items-center space-x-2">
                          {evidenceFile.uploaded ? (
                            <div className="flex items-center space-x-1 text-green-600">
                              <Check className="h-4 w-4" />
                              <span className="text-xs">Uploaded</span>
                            </div>
                          ) : (
                            <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                          )}
                          
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(evidenceFile.id)}
                            className="h-8 w-8 p-0 hover:bg-red-50 hover:text-red-600"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Guidelines */}
          <div className="mt-6 p-4 bg-blue-50 rounded-xl">
            <h4 className="font-medium text-blue-900 mb-2">Evidence Guidelines</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Include before/after photos showing environmental changes</li>
              <li>• Provide documentation of conservation activities</li>
              <li>• Add videos demonstrating project implementation</li>
              <li>• Include any relevant permits or certifications</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default EvidenceUploader;