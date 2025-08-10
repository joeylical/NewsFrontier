-- vim.lsp.config.pylsp = nil
-- vim.lsp.config.pylsp.cmd = {
--   'uv', 'run', '--with', 'python-lsp-server', 'pylsp'
-- }
--
-- vim.lsp.enable('pylsp')

-- vim.lsp.start({
--   name = 'pylsp',
--   cmd = {'uv', 'run', '--with', 'python-lsp-server', 'pylsp'},
--   root_dir = vim.fs.root(0, {'pyproject.toml'}),
-- })

require('lspconfig').pylsp.setup({
  cmd = {'uv', 'run', '--with', 'python-lsp-server', 'pylsp'}
})

local capabilities = require('cmp_nvim_lsp').default_capabilities()
require('lspconfig')['ts_ls'].setup {
  capabilities = capabilities
}

require('lspconfig')['html'].setup {
  capabilities = capabilities
}

-- require('lspconfig').ruff.setup({
--   init_options = {
--     settings = {
--       -- Ruff language server settings go here
--     }
--   }
-- })
