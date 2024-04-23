import tarfile


def create_tarball(source_dir, tar_path):
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(source_dir, arcname="")
