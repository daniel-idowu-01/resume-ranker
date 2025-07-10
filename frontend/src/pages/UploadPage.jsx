import { useNavigate } from "react-router-dom";
import UploadForm from "../components/UploadForm";

const UploadPage = () => {
  const navigate = useNavigate();

  const handleUpload = async (formData) => {
    try {
      console.log("Files in formData:", formData.getAll("resumes"));
      console.log("Job description:", formData.get("job_description"));

      const response = await fetch("http://127.0.0.1:8000/api/upload-resumes", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log("Upload successful:", result.job_id);

      navigate(`/results/${result.job_id}`, {
        state: { jobId: result.job_id },
      });
    } catch (error) {
      console.error("Upload failed:", error);
      throw error;
    }
  };

  return <UploadForm onSubmit={handleUpload} />;
};

export default UploadPage;
