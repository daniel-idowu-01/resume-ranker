import { useNavigate } from "react-router-dom";
import UploadForm from "../components/UploadForm";

const UploadPage = () => {
  const navigate = useNavigate();

  const handleUpload = async (formData) => {
    const response = await fetch("http://localhost:8000/api/upload-resumes", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      const result = await response.json();
      console.log("Upload successful:", result.job_id);

      // Navigate to the results page with the job ID
      navigate(`/results/${result.job_id}`, {
        state: { jobId: result.job_id },
      });
    }
  };
  return <UploadForm onSubmit={handleUpload} />;
};

export default UploadPage;
