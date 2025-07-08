export default class ResumeRankingClient {
  constructor(baseUrl = "http://localhost:8000") {
    this.baseUrl = baseUrl;
  }

  /**
   * Upload resumes and job description for ranking
   * @param {FileList} resumeFiles - List of PDF files
   * @param {string} jobDescription - Job description text
   * @returns {Promise<Object>} Response with job_id and status
   */
  async uploadResumes(resumeFiles, jobDescription) {
    try {
      const formData = new FormData();

      // Add job description
      formData.append("job_description", jobDescription);

      // Add resume files
      for (let i = 0; i < resumeFiles.length; i++) {
        formData.append("resumes", resumeFiles[i]);
      }

      const response = await fetch(`${this.baseUrl}/api/upload-resumes`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      return await response.json();
    } catch (error) {
      console.error("Error uploading resumes:", error);
      throw error;
    }
  }

  /**
   * Get job processing status
   * @param {string} jobId - Job ID returned from upload
   * @returns {Promise<Object>} Job status and progress
   */
  async getJobStatus(jobId) {
    try {
      const response = await fetch(`${this.baseUrl}/api/job-status/${jobId}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to get job status");
      }

      return await response.json();
    } catch (error) {
      console.error("Error getting job status:", error);
      throw error;
    }
  }

  /**
   * Get detailed job results
   * @param {string} jobId - Job ID
   * @returns {Promise<Object>} Detailed results with rankings
   */
  async getJobResults(jobId) {
    try {
      const response = await fetch(`${this.baseUrl}/api/job-results/${jobId}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to get job results");
      }

      return await response.json();
    } catch (error) {
      console.error("Error getting job results:", error);
      throw error;
    }
  }

  /**
   * Clean up job data
   * @param {string} jobId - Job ID
   * @returns {Promise<Object>} Cleanup confirmation
   */
  async cleanupJob(jobId) {
    try {
      const response = await fetch(`${this.baseUrl}/api/job/${jobId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to cleanup job");
      }

      return await response.json();
    } catch (error) {
      console.error("Error cleaning up job:", error);
      throw error;
    }
  }

  /**
   * Poll job status until completion
   * @param {string} jobId - Job ID
   * @param {Function} onProgress - Callback for progress updates
   * @param {number} pollInterval - Poll interval in milliseconds
   * @returns {Promise<Object>} Final job status
   */
  async pollJobStatus(jobId, onProgress = null, pollInterval = 2000) {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await this.getJobStatus(jobId);

          if (onProgress) {
            onProgress(status);
          }

          if (status.status === "completed") {
            resolve(status);
          } else if (status.status === "failed") {
            reject(new Error(status.message || "Job failed"));
          } else {
            // Continue polling
            setTimeout(poll, pollInterval);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }
}
