# Automatic Deployment

An ansible playbook is provided to deploy to production and staging environments.
GitHub actions is configured to automatically deploy main branch to production.

The server was set up manually with nginx and certbot, see the main readme
for the resulting nginx config.

Run ansible using

```
ansible-playbook -i deployment/production_inventory.ini deployment/deploy.yml
```

from the repository root.
Replace `production` with `staging` for staging environment.
Secrets can be configured locally in `deployment/group_vars/production`
like so:

```yaml
---
gitlab_key: "..."
gitlab_secret: "..."
django_secret: "..."
```

Do not commit those! They are also stored as GitHub repository secrets for CI.
