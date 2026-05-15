project {
  name             = "da-vinci"
  default_platform = "claude-code"

  git_exclude = true
}

registry "climb" {
  url = "s3://climb-dex-registry"

  config = {
    region = "us-east-1"
  }
}

package "code-review" {}

package "python-dev" {}
