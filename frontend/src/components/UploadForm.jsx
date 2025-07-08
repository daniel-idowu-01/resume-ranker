import { useState } from "react";
import { Upload, File, Delete, Loading } from "./svgs";
import { formatFileSize } from "../utils/helpers";

const UploadForm = ({ onSubmit }) => {
  const [resumes, setResumes] = useState([]);
  const [jobDescription, setJobDescription] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleResumeUpload = (e) => {
    const files = Array.from(e.target.files);
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

  const handleJobDescriptionChange = (e) => {
    setJobDescription(e.target.value);
    if (e.target.value.trim()) {
      setErrors((prev) => ({ ...prev, jobDescription: null }));
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

    if (!jobDescription.trim()) {
      newErrors.jobDescription = "Job description is required";
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

      // Add resumes to form data
      resumes.forEach((resume, index) => {
        formData.append(`resumes`, resume);
      });

      // Add job description
      formData.append("jobDescription", jobDescription);

      // Call parent component's onSubmit handler
      await onSubmit(formData);

      // Reset form on success
      setResumes([]);
      setJobDescription("");
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
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        Upload Resumes for Ranking
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Resume Upload Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Resumes (PDF only)
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
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
              className="cursor-pointer flex flex-col items-center"
            >
              <Upload />
              <span className="text-sm text-gray-600">
                Click to upload or drag and drop
              </span>
              <span className="text-xs text-gray-500 mt-1">
                PDF files only, max 10 files
              </span>
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
            <div className="space-y-2">
              {resumes.map((resume, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <File />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
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
                    className="text-red-500 hover:text-red-700 transition-colors"
                    disabled={isUploading}
                  >
                    <Delete />
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
          </label>
          <textarea
            id="job-description"
            value={jobDescription}
            onChange={handleJobDescriptionChange}
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Paste the job description here..."
            disabled={isUploading}
          />
          {errors.jobDescription && (
            <p className="mt-2 text-sm text-red-600">{errors.jobDescription}</p>
          )}
        </div>

        {/* Submit Button */}
        <div>
          <button
            type="submit"
            disabled={isUploading}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isUploading ? (
              <>
                <Loading />
                Processing...
              </>
            ) : (
              "Rank Resumes"
            )}
          </button>
        </div>

        {/* Submit Error */}
        {errors.submit && (
          <p className="text-sm text-red-600 text-center">{errors.submit}</p>
        )}
      </form>
    </div>
  );
};

export default UploadForm;
