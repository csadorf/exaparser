import os
import re

from multiprocessing import Pool
from endpoints.jobs import JobEndpoints
from endpoints.projects import ProjectEndpoints
from endpoints.materials import MaterialEndpoints
from endpoints.raw_properties import RawPropertiesEndpoints

from src import settings
from src.data import DataHandler
from src.utils import upload_file


class ExabyteRESTFulAPIDataHandler(DataHandler):
    """
    Exabyte RESTFul API data handler class.


    Args:
        job (src.job.Job)
    """

    def __init__(self, job):
        super(ExabyteRESTFulAPIDataHandler, self).__init__(job)
        self._owner = self._project = None
        self.job_endpoints = JobEndpoints(*self.endpoint_args)
        self.project_endpoints = ProjectEndpoints(*self.endpoint_args)
        self.material_endpoints = MaterialEndpoints(*self.endpoint_args)
        self.raw_properties_endpoints = RawPropertiesEndpoints(*self.endpoint_args)

    @property
    def endpoint_args(self):
        """
        Returns a list of arguments passed to the endpoints.

        Returns:
             list
        """
        return [settings.API_HOSTNAME, settings.API_PORT, settings.API_ACCOUNT_ID,
                settings.API_AUTH_TOKEN, settings.API_VERSION, settings.API_SECURE]

    @property
    def owner(self):
        """
        Returns the owner configuration extracted from the project.

        Returns:
             dict
        """
        if not self._owner:
            self._owner = self.project["owner"]
        return self._owner

    @property
    def project(self):
        """
        Returns the project the job should be created in.

        Returns:
             dict
        """
        if not self._project:
            self._project = self.project_endpoints.list(
                {
                    "slug": settings.PROJECT_SLUG,
                    "owner.slug": settings.OWNER_SLUG
                }
            )[0]
        return self._project

    def create_materials(self):
        """
        Creates materials in web application.

        Returns:
             list
        """
        materials = []
        for config in self.job.materials:
            config["owner"] = self.owner
            materials.append(self.material_endpoints.create(config))
        return materials

    def create_job(self, materials):
        """
        Creates job in web application.

        Note: job must be set as external (isExternal=True) to be able to access the files.

        Returns:
             list
        """
        config = self.job.to_json()
        config["isExternal"] = True
        config["owner"] = self.owner
        config["_project"] = {"_id": self.project["_id"]}
        config["_material"] = {"_id": materials[0]["_id"]}
        return self.job_endpoints.create(config)

    def create_properties(self, job_id):
        """
        Creates properties in web application. Properties will be shown in job's results tab after creation.

        Args:
            job_id (str): job ID.
        """
        for property_ in self.job.properties:
            property_["source"]["info"]["jobId"] = job_id
            self.raw_properties_endpoints.create(property_)

    @property
    def files(self):
        """
        Returns a list file paths relative to jb working directory to upload to object storage.

        Note: files matching settings.EXCLUDED_FILES_REGEX are ignored.

        Returns:
             list
        """
        files_ = []
        for root, dirs, files in os.walk(self.job.work_dir):
            for file_ in [os.path.join(root, f) for f in files]:
                if settings.EXCLUDED_FILES_REGEX and re.match(settings.EXCLUDED_FILES_REGEX, file_): continue
                files_.append(file_.replace("".join((self.job.work_dir, "/")), ""))
        return files_

    def upload_files(self, job_id):
        """
        Uploads the file in parallel into object storage.

        Note: permission to upload files into object storage is given through presignedURLs.

        Args:
            job_id (str): job ID.
        """
        presigned_urls = self.job_endpoints.get_presigned_urls(job_id, self.files)
        presigned_urls = [{"path": os.path.join(self.job.work_dir, p["file"]), "URL": p["URL"]} for p in presigned_urls]
        num_workers = min(len(presigned_urls), settings.NUM_WORKERS)
        pool = Pool(processes=num_workers)
        pool.map(upload_file, presigned_urls)

    def handle(self):
        """
        Creates materials, job and properties in webapp and uploads files into object storage.
        """
        materials = self.create_materials()
        job = self.create_job(materials)
        self.create_properties(job["_id"])
        if settings.UPLOAD_FILES:
            self.upload_files(job["_id"])
