# Ansible scaffold

This folder contains a minimal Ansible scaffold intended for post-provisioning
configuration tasks after Terraform creates infrastructure. It's small by
design — replace with role-based structure for larger projects.

Quickstart (from repository root, PowerShell):

```powershell
cd infra/ansible
# Run using an inventory file; replace hosts and user accordingly
ansible-playbook -i inventory.ini playbook.yml
```

Notes
- For cloud-hosted infrastructure prefer dynamic inventory (AWS EC2 plugin)
  or use Terraform to write inventory outputs consumed by Ansible.
- For idempotent role-based designs, break tasks into roles under `roles/`.
