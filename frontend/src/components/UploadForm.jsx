import { useState, useCallback } from "react";
import { Upload, File, Delete, Loading } from "./svgs";
import { formatFileSize } from "../utils/helpers";

const UploadForm = ({ onSubmit }) => {
  const [resumes, setResumes] = useState([]);
  const [job_description, setjob_description] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [errors, setErrors] = useState({});
  const [isDragging, setIsDragging] = useState(false);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (isUploading) return;

      const files = Array.from(e.dataTransfer.files);
      handleFileValidation(files);
    },
    [isUploading]
  );

  const handleFileValidation = (files) => {
    const pdfFiles = files.filter((file) => file.type === "application/pdf");

    if (pdfFiles.length !== files.length) {
      setErrors((prev) => ({
        ...prev,
        resumes: "Only PDF files are allowed for resumes",
      }));
      return;
    }

    if (pdfFiles.length > 10) {
      setErrors((prev) => ({
        ...prev,
        resumes: "Maximum 10 resumes allowed",
      }));
      return;
    }

    setResumes(pdfFiles);
    setErrors((prev) => ({ ...prev, resumes: null }));
  };

  const handleResumeUpload = (e) => {
    const files = Array.from(e.target.files);
    handleFileValidation(files);
  };

  const handlejob_descriptionChange = (e) => {
    setjob_description(e.target.value);
    if (e.target.value.trim()) {
      setErrors((prev) => ({ ...prev, job_description: null }));
    }
  };

  const removeResume = (index) => {
    setResumes((prev) => prev.filter((_, i) => i !== index));
  };

  const validateForm = () => {
    const newErrors = {};

    if (resumes.length === 0) {
      newErrors.resumes = "Please upload at least one resume";
    }

    if (!job_description.trim()) {
      newErrors.job_description = "Job description is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsUploading(true);

    try {
      const formData = new FormData();

      resumes.forEach((resume) => {
        formData.append(`resumes`, resume);
      });

      formData.append("job_description", job_description);

      await onSubmit(formData);

      // Reset form on success
      setResumes([]);
      setjob_description("");
      setErrors({});
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        submit: "Failed to upload. Please try again.",
      }));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg border border-gray-100">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        Upload Resumes for Ranking
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Resume Upload Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Resumes (PDF only)
          </label>
          <div
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 ${
              isDragging
                ? "border-blue-500 bg-blue-50"
                : "border-gray-300 hover:border-gray-400"
            }`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input
              type="file"
              multiple
              accept=".pdf"
              onChange={handleResumeUpload}
              className="hidden"
              id="resume-upload"
              disabled={isUploading}
            />
            <label
              htmlFor="resume-upload"
              className="cursor-pointer flex flex-col items-center space-y-3"
            >
              <div
                className={` rounded-full ${
                  isDragging ? " text-blue-600" : " text-gray-600"
                }`}
              >
                <Upload className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <span className="text-sm font-medium text-gray-600">
                  {isDragging
                    ? "Drop files here"
                    : "Click to upload or drag and drop"}
                </span>
                <p className="text-xs text-gray-500">
                  PDF files only, max 10 files (up to 5MB each)
                </p>
              </div>
            </label>
          </div>
          {errors.resumes && (
            <p className="mt-2 text-sm text-red-600">{errors.resumes}</p>
          )}
        </div>

        {/* Uploaded Resumes List */}
        {resumes.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Uploaded Resumes ({resumes.length})
            </h3>
            <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
              {resumes.map((resume, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="p-2 bg-white rounded-lg border border-gray-200">
                      <File className="w-4 h-4 text-gray-500" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {resume.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(resume.size)}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeResume(index)}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors rounded-full hover:bg-gray-200"
                    disabled={isUploading}
                    aria-label="Remove file"
                  >
                    <Delete className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Job Description Section */}
        <div>
          <label
            htmlFor="job-description"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Job Description
            <span className="text-red-500 ml-1">*</span>
          </label>
          <textarea
            id="job-description"
            value={job_description}
            onChange={handlejob_descriptionChange}
            rows={8}
            className={`w-full px-3 py-2 border ${
              errors.job_description ? "border-red-300" : "border-gray-300"
            } rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all`}
            placeholder="Paste the job description here..."
            disabled={isUploading}
          />
          {errors.job_description && (
            <p className="mt-2 text-sm text-red-600">
              {errors.job_description}
            </p>
          )}
        </div>

        {/* Submit Button */}
        <div>
          <button
            type="submit"
            disabled={
              isUploading || resumes.length === 0 || !job_description.trim()
            }
            className={`w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
              isUploading ? "bg-blue-400" : "bg-blue-600 hover:bg-blue-700"
            } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all`}
          >
            {isUploading ? (
              <>
                <Loading className="animate-spin mr-2 w-4 h-4" />
                Processing...
              </>
            ) : (
              "Rank Resumes"
            )}
          </button>
        </div>

        {/* Submit Error */}
        {errors.submit && (
          <div className="p-3 bg-red-50 rounded-lg">
            <p className="text-sm text-red-600 text-center">{errors.submit}</p>
          </div>
        )}
      </form>
    </div>
  );
};

export default UploadForm;
