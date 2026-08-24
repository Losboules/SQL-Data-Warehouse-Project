# Northstar Retail File Manifest

Generated: `2026-08-17T00:13:16+00:00`

`FILE_MANIFEST.md` is intentionally excluded from its own hash listing.

Files listed: **198**  
Total listed size: **30,078,928 bytes**

| Path | Bytes | SHA-256 | Purpose |
|---|---:|---|---|
| `.env.example` | 1,024 | `bc1d1efbcf8fcc5fd1fc7ef7a64b92ff2d8f535ad52b757172c84aff45e5e0d0` | Safe non-secret environment-variable template |
| `.github/workflows/validate_project.yml` | 1,593 | `5afb65feed06e3f2a39e60d57033fe2aa7d5015b01c938e39a7fe658d8a7e85f` | GitHub Actions validation workflow |
| `.gitignore` | 649 | `fca4b8289fa248ccd596637435be594ae1d4c10518f3a96f89be763d41d3b826` | Git exclusions for secrets, local data, caches, and generated artifacts |
| `config/data_generation.yml` | 1,173 | `124bc52ae3f4dbfeaf5a5c30fe855fd73eeffc5e27ca202c2a4340e5e802d729` | Non-secret generation or runtime configuration example |
| `config/dev.example.yml` | 651 | `f997597f278d616201e77b0820fb9cf171a07617fcdea673ad0abcffa64f7125` | Non-secret generation or runtime configuration example |
| `config/logging.yml` | 239 | `9bf4a7779bd3b54c961dcf94f23b942faf6d17066917211b72cf52460e166d7c` | Non-secret generation or runtime configuration example |
| `databricks/jobs/job_definition.example.yml` | 6,772 | `b375f1524d68081704de407b5e7e801d1eb179e71bddc9918b0d57d5d756b690` | Version-controlled Lakeflow Job dependency definition |
| `databricks/jobs/job_task_map.md` | 868 | `c0e7fa556adc3da6f4ab7b568b312673c9ab6e0d895129d9b8617be7a5b9bf47` | Version-controlled Lakeflow Job dependency definition |
| `databricks/notebooks/00_environment_check.py` | 3,197 | `596f92cdae23ffd3ff699fad82134d2554f1e295c04ead9ca510b30c604e1fd3` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/01_bronze_sqlserver.py` | 3,175 | `422c7af63087486170ba61884f8deb554772445f2951606b6fb44c369c064425` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/02_bronze_postgres.py` | 3,069 | `cde4fbc18da212eda208f1297e235f45307b3dfbc7b475197dfa9bb67b3e026d` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/03_bronze_files.py` | 3,920 | `68dbb4a4d29f9ca6b39a5f1921cba1b51d458538f69be01c9c6e1c2623fe2f7d` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/04_silver_customers.py` | 7,437 | `b1841c76e33a4a21482413f4b00eb5b56722c337d83baf69b61425a8936e0249` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/05_silver_products.py` | 8,442 | `e2a60720841e1219718569f4f84b946e24cb7f3eadd75721217307ca799ff44f` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/06_silver_sales.py` | 13,909 | `fd935c459243e96c8d9c6d43a38139e189fa8f62403216ee9c4401a2bcb2558a` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/07_silver_digital.py` | 12,648 | `bafb61ecf0332198e32288c870feeaa408baca500823ac5d0d0e6fa1884b7dee` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/08_gold_dimensions.py` | 21,545 | `f7f57473357cc861a36fd1fc154ee84c94fb47c64b7a518200f27a6bdb8a470e` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/09_gold_facts.py` | 23,328 | `401f35f3eb10fe749a26c75df5d1ed04ece82564b13b2028ed2f44c82c94f5b7` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/10_data_quality.py` | 11,481 | `3277f9bd3bbad18e60f6a885e94ff8362f11efd649bcdc124b163ff21d16a1da` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/11_publish_gold.py` | 3,192 | `77ce779a8ca42ba9220404a5cd7e7e91ab25b0b9e0bb205d32592128f159f6d0` | Databricks source notebook for the numbered pipeline task |
| `databricks/notebooks/12_demo_queries.py` | 3,813 | `7cf4942a235f428044566be307d2c7f485a37f42e5c0356a9871150ff7917964` | Databricks source notebook for the numbered pipeline task |
| `databricks/README.md` | 865 | `1e7513058c9e458a6eff6101e688228cfaac3cf46c4567f0dcb976161682794c` | Project support artifact |
| `datasets/demo_gold/dim_campaign.csv` | 1,494 | `7bf68ddb8a235e77bb2106d7c3ea28551fbdee7b88cc484292ae3ae774710dbd` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/dim_channel.csv` | 1,010 | `654d21122fe8d2cc95478353ee1766e76de22c598ea686c1fdfc32d0c8573782` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/dim_customer.csv` | 15,283 | `4d8cd027f8863a0aa43692e73c2ba55c7805091c68c3343dfda9a728c6b94e07` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/dim_date.csv` | 459,758 | `5667b82bf8c06f4c2c7335b56c0916a6b601c20bbff513c9b284ba4a9deb35fe` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/dim_employee.csv` | 2,914 | `68f2758ceebc74c05a38d85d6f18246cba90db7df03747b7fbc1dfea49708774` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/dim_product.csv` | 8,213 | `b0e3ebff8605a0a54ea3ae8ceb1672fb549298ad49fe30847df95cbfe560b8a5` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/dim_promotion.csv` | 653 | `dffe50d4008448a7c47174894148169ac62eb871b59294482800a189ce4cccbe` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/dim_store.csv` | 958 | `cd90360315cb4408e2eb742c9a948980abfcf5050f3bddb59cf6eab9353b8bbf` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/dim_supplier.csv` | 1,272 | `62b8c9412910f49fb175cca44edad0c27dc6c1a9feac4abea6a64e027c7810a1` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/fact_inventory_snapshot.csv` | 7,572 | `f1f7ef60429496d6e3dd3a436937f037a984be0bd5ad920eca5b03c7e6f26a9f` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/fact_marketing_spend.csv` | 57,434 | `36b4bd2d7377bfc90f3c74886b54a9c13ff56b9ba2fd9b018cb54712a4d1c9b3` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/fact_returns.csv` | 6,267 | `535c9e9a357c1ea2b9873cd444abb409e9bb97ef2d4ce2d5b9902c3d46c0e9e7` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/fact_sales.csv` | 95,199 | `25f2ab0f09b7153e29a86a104a413bf8e3636073b20544b6d68598b522c5e6de` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/fact_shipments.csv` | 20,400 | `aac38c910f16c01c1b690bb989ebdaf48acb0812ce792e00c4cf94fe1cc1c2db` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/fact_web_sessions.csv` | 46,102 | `f09ab3b5ec67061e4867983cb74eb51ebe4af631b7a28cbff1a76463ae2fff45` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/gold_manifest.json` | 8,133 | `6cca5f4d31e2fd8259bb7465b07cbbcf1aa6fb865e7cbc1bafa44bfe013c16f2` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/quality_results.json` | 13,442 | `0911368db9a5a4da5cb960a432a5aa3acfd02d8631adcd15f71d703ae3a89e39` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/demo_gold/reconciliation_results.json` | 440 | `3da2c3982addef4fbf3adebef24ac8dfce126ec858497e3b982d83ff578573ff` | Locally validated Gold dimension, fact, quality, or reconciliation evidence |
| `datasets/generated/.gitkeep` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Keeps an intentionally empty directory in Git |
| `datasets/raw/.gitkeep` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Keeps an intentionally empty directory in Git |
| `datasets/sample/files/promotion_calendar.csv` | 289 | `822f6bb2c2148c7fcf1f6cccad38ab489b6ae6fa8089cee41951e9948d84f4f0` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/files/returns.csv` | 3,068 | `224d4d1949b87ecc90c5f84c06f4ad0868a30cb6eae09d1ee5a2e0605cce18fe` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/files/shipment_tracking_events.jsonl` | 50,447 | `a9437bfcb1205d67489294d539619c50c026505cad3e7c4d21a57cc178e5cb68` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/files/supplier_cost_updates.csv` | 1,822 | `7c50709adc8525a851b1bece967c1669c53754917cd359e3dc423270f3feec24` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/metadata/batch_manifest.json` | 4,598 | `94fd8a0043b3c11592ecaaa893828af44dae7aab68252967e3885d8d470d804e` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/metadata/expected_quality_issues.json` | 776 | `9070cb3a906c866d47d82ea15a6b7753690eecb8dc0fda06142c35f5d0fa057d` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/metadata/generation_summary.csv` | 711 | `bd7c1727de6ed4cb6a870cc8d40603766d4ade423b68c157db067467186d4517` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/metadata/validation_results.json` | 455 | `ec483b1bae714d80ed4dcb7634e2e1dda3dfd557f8624d60630f7cde59abce72` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/postgres/campaign_touchpoints.csv` | 12,896 | `7d1ba8e02a26aa014d002535359c9a1dd3b70f10b3d1c2390a991044f6f39ec5` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/postgres/campaigns.csv` | 1,071 | `51f90fd3c032cb02f6048831c3b5ba2b3ca824f623138a9a9906a5d53b5af51c` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/postgres/marketing_spend.csv` | 32,169 | `ea71b597f72685f3303c52e12b15a7cc916f732e2c07d922b4f94983e5f8e82c` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/postgres/web_events.csv` | 122,828 | `f959ece2ee5e1d7109d76fc8d0ee383d4a54c5ef257444a9dffee41e469d20ec` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/postgres/web_sessions.csv` | 35,193 | `0bca916d6d860a87cecc120c12d5caeff3a7a4d790022a8f1efb9015e0dae691` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/postgres/web_users.csv` | 12,093 | `83eaefa388f821b06d5ab8b0f0879524095c41a95f295f6a3b35587b852ef1b6` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/addresses.csv` | 6,796 | `8ee53eb3946801bd0f73c82ce88b4ebe4bb7cc32331803709498aa54c33c86f4` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/customers.csv` | 8,318 | `e2eaff3422366954d8ecaa68183a816e775f2da21c40a39507415453ad15638a` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/employees.csv` | 2,214 | `2d3827b7e4c1bd17e332b257dc2d997d96cab3a2a8d8fc74cfc9442dfb41eeed` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/inventory_snapshots.csv` | 3,000 | `248f420b338c410fe9c446ae8720882742e059a0b87c13e5b69c0746d99d9c13` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/inventory_transactions.csv` | 14,608 | `0a77f9fbd4f6acc036232f254801732dd06dd6dc113cdb596053eb0df72a1a1e` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/order_items.csv` | 35,369 | `cf41034c8c4b6fb14216c6443f2a95f965a13c97e2dd8de305c056645292b756` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/orders.csv` | 24,535 | `f373a6bae9a9f97bf04f4904eea7bf8bcdd346ec50ed84df76a5f6d2f17e58c2` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/payments.csv` | 25,107 | `9fcd8da198f8e0c06c64b18992af81c27b61609f0ed6cb8fd2709ba0b2ef4b93` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/product_categories.csv` | 493 | `bbefba70ab0051f9b8dcfa1c6b3f0f876ec4da57b5017aa2282f8113cac17c46` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/products.csv` | 3,721 | `c376d91df4e1c7db319a9ce8c0adbd21ab06abf225eebdca1d3e10b42cd42345` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/shipments.csv` | 14,337 | `bb7165989456602ec17c53c5de4942607161e549e915b890f7e635435ec0833f` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/stores.csv` | 660 | `0149522a79b6165d9d0b322e21f9642217b47656750fa02b2c1c451b797dc823` | Deterministic fictional source fixture or its audit metadata |
| `datasets/sample/sqlserver/suppliers.csv` | 861 | `c58ffb3b52a23bae2a085b189d9cb31ce9fe5995279b6e7c9a5f6a76e00ca38e` | Deterministic fictional source fixture or its audit metadata |
| `datasets/state/.gitkeep` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Keeps an intentionally empty directory in Git |
| `docs/architecture.md` | 3,470 | `96d9694d0e7ef5300afd74ca8a02ae85dd95ba322c2255c61bd91bc678824091` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/assumption_log.md` | 1,560 | `46cd8221c22b98daae582252ced184c5a2b1e78f3770612d459c778919a5f0d9` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/business_requirements.md` | 6,699 | `e12eae83fd445054160ec4ab5d9ca447f93b9a2090363c9042587887f6414af9` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/claim_to_evidence_map.md` | 1,205 | `a4af0fe0530735e6ad3ac63bb2865eac147739f77cf1717613fee82e7804e07a` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/data_dictionary.csv` | 59,683 | `bb6d7233ed4f204cffdcffb9250e4be2687e091bc3c0289e5f41066b37b2488b` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/data_dictionary.md` | 137,482 | `0f76cc189c40873187b6c0f1c4ffd76d7e292abb02194cd7991a601da22adb8e` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/data_lineage.md` | 1,394 | `3489a5bff006ec58580c906c236f699a2d275c142afadb0e3f0ba076bea51aaa` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/demo_video_script.md` | 1,807 | `77d603d84f983ce8ff9c98342224e943f3b5d81de589ce6ff5ef03b75747302e` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/EXECUTION_STATUS.md` | 2,258 | `2d074cc1a5ede714254e8b3f2908731191d47285423747fb5fed00b2f52d1c4a` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/images/cloud_connected_flow.dot` | 681 | `b9f53a79684eb742bc62d58aeb689136509ce03dec7dc7cb08df5129a9b4d363` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/cloud_connected_flow.mmd` | 265 | `1e22fb322188e09e58781adde00b29fdaaf1e0240f160f1f3fb090401392ba48` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/cloud_connected_flow.svg` | 6,488 | `e42cca39146e76dc8f0ea4341e9b496ecb565428b0516de370e5b498f58f6cbc` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/gold_star_schema.dot` | 1,445 | `3fbe300216a77d66a4fa35e791d51da871d2714729985f26c094e1c66b6fd2f6` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/gold_star_schema.mmd` | 601 | `e221f3342939b7119699947f7ed39eb1208567c69667d6a530ee2d3c5cde15aa` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/gold_star_schema.svg` | 17,532 | `989bcb22c3603f2d9ac6aec2949591abbf1d5fe40a7df21dd33c93438ee76065` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/jobs_dependency.dot` | 753 | `8c05424cb8939a5bc25e4718a198fcfadbc8142bcb233fd0c83914b2910c365d` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/jobs_dependency.mmd` | 437 | `3c8f91332a127e747892182119cd69c0ee1d4edea4c404c1f215c1433f2556df` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/jobs_dependency.svg` | 13,013 | `8da8e449bac65af6cb8abc01a8563e0c1ba5b00b80d3f903a5fc388d327c78ab` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/lineage.dot` | 753 | `f6c05cd2b6a1267566600b9396b2f5561ad7b021ae5871d51a0d9a502199d350` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/lineage.mmd` | 292 | `cbc4957fef4290b906a7ed3de020e8358281f0e651b3480eaf927beb27f2f609` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/lineage.svg` | 7,884 | `7eb9c0bac87c070eaa1952ff8853455913b2ae93dd4ae12bd50ad8a5125e7419` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/local_first_flow.dot` | 724 | `e41b159d39f75bc4d0f7e5bdd641cd72a531e42160dbe747adfa07dae92e4573` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/local_first_flow.mmd` | 365 | `bb3b66301ba003a77491cf3ce408f4d9447cbe234236b2aaa05523056517af3f` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/local_first_flow.svg` | 6,827 | `e4435826584e37cd59f5392049e6972e26c8573ad63e76e884609f200244fea6` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/overall_architecture.dot` | 1,133 | `0dcf5f16e593c8f50377d75131a45698f6203a624ff51ad4c5a06339815d3d9d` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/overall_architecture.mmd` | 395 | `46899d9638a9462a13851b20b844b8e35ab2e8d54bda59b1658f90b08e4132f4` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/overall_architecture.svg` | 10,879 | `f58f7bcb44a73b49b7ff1646d0b0b930e4074ba5443285e710142954be8fe0d2` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/postgres_erd.dot` | 916 | `193e5cea63a9f0236c7a8f547be8ad204010b4d9e662e7202ddab7934e2dc38b` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/postgres_erd.mmd` | 339 | `27cfe1d189b72b852e5eab6cc16d06d079a47f71c15f02deccf10ff72a337286` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/postgres_erd.svg` | 8,857 | `a0e36a95456935707ca05c9a979435fb42a65e5b6f650924083e0258d2108510` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/README.md` | 286 | `740cc8dd1adbf9afdcc62bb0dcfa39e6541a34bce97d4f14a04a4d76ef5baa65` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/scd2_timeline.dot` | 415 | `fb8d9a4cb34e0c4de88809ca83531c8121849c50d824c9bea29d6f7f5b44d32c` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/scd2_timeline.mmd` | 161 | `51ee3f09cefe0a2b614684b8cebaee081fde34bb9ef4f30b2b9a758783e96178` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/scd2_timeline.svg` | 3,585 | `39837f260fdc629cfb71ca8563eac10fa9c027f742bfc11f0c6a887b5f1c47ef` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/sqlserver_erd.dot` | 1,568 | `b0c44ba845645de763e70c7712f848b4b61c1c9a81802e844a20adbff437f89b` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/sqlserver_erd.mmd` | 481 | `c7214fc8d7468383f4a38bda490a9804c6af502eac5242b421558233a3c1b9d4` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/images/sqlserver_erd.svg` | 16,701 | `86ba3999a6341f6011254d954e419a5b9730356bb0a116e9564a40f046df7437` | Architecture, lineage, ERD, job, or dimensional-model diagram asset |
| `docs/interview_walkthrough.md` | 25,292 | `6d3175ed0bdcbe1efa8dd3fdcbbb6384625abc8744b366c1367e2fd9b53cfd9b` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/kpi_definitions.csv` | 2,578 | `a5b263c161ac2b352d6f267d1e079b277782fda05ce7b17eff8ad3747338149f` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/kpi_definitions.md` | 4,017 | `d40820969203ffc2da9f0ff141e8d6b4a568413bdb22ebc07f9e84022e2517e4` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/linkedin_post.md` | 1,438 | `a9fbb2b85ec7d8fb3212d32db2cae691e492d940c85cf0295424218144d57b29` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/LOCAL_VALIDATION_REPORT.md` | 5,863 | `44d565ea90e1baf1e7286add2d585053bc95bea4ad339212eac2cac08b2db75d` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/manual/Northstar_Retail_Complete_Manual_Build_Workbook.md` | 13,250,779 | `d18618c3a22e0c8a43efc7bc58f9ce3c1103d47d42b37a5b0362b02f3ba9eda2` | Complete beginner build manual reference |
| `docs/manual/Northstar_Retail_Complete_Manual_Build_Workbook.pdf` | 14,424,374 | `4d50aa0fd0c3005089c389dd100b4de518606ed1c604710ae872f35eff09d2ee` | Complete beginner build manual reference |
| `docs/official_sources.md` | 3,988 | `f98885c7881ece69f62a9ab40ec8fe8a71763a86aa3f1a9f6d7f8ba5f5d51ab6` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/optional_extensions.md` | 2,673 | `bdfff937054798b7f331cb38494ec99454ad7b6df9357f059da519d653ed10e9` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/repository_current_state.md` | 1,577 | `b8b187e3b2b983972c8650bad3935391c7c7ae0783788c63609097ee1b02f65b` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/repository_migration_plan.md` | 1,847 | `e84731537882e307cee6dbfbe0aaf52da3f0fb53ae773f734d5fa4d0a6a3f855` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/resume_bullets.md` | 1,816 | `87f955b3f45bd2d37dabc84d39c1527ed105a176e9ef4e95ebb4741103c77450` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/risk_register.md` | 2,073 | `a9e5904bb2951e6e4537b493e23da863d58266bf5fa6306c8149268fa54cb57f` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/runbook.md` | 2,126 | `6a0a425f64830bc36038b4d287639a3cd1932422805dab6f9f43bc012ebca7a0` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/security_and_cost.md` | 3,223 | `af948031cba5d7313724265aabf8841a253e22c60ec35ce85e2375c47c7565ed` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/source_to_target_mapping.csv` | 2,168 | `b9f5d29d8419187e9b9f1491f33a1ade5b946bd2caef49f18f289ca85ff38814` | Technical, governance, portfolio, validation, or operating documentation |
| `docs/source_to_target_mapping.md` | 4,009 | `f8607a22c8f6591158b4f4c3d7c0e385af258b5299550ff3e21d10feb0f0131f` | Technical, governance, portfolio, validation, or operating documentation |
| `LICENSE` | 1,071 | `c1c77e61db6c30ff4813bce4700ebc6cc4b33af5a2fc5d6a95587c286363ffae` | MIT license |
| `logs/.gitkeep` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Keeps an intentionally empty directory in Git |
| `notebooks/Northstar_Retail_Local_Validation_Demo.executed.ipynb` | 78,319 | `5f98fee72cfc57cf06e01ae5542804adb932c4e799c20bce76c26568c40bfc7d` | Local showcase notebook source, executed output, or HTML rendering |
| `notebooks/Northstar_Retail_Local_Validation_Demo.html` | 361,431 | `4b46affcc7cd3f03a50833de9635b1e95217dd106182c60fed7a199a050a9f5c` | Local showcase notebook source, executed output, or HTML rendering |
| `notebooks/Northstar_Retail_Local_Validation_Demo.ipynb` | 4,939 | `4521584c3f8821d3156ef6ca7129c70baa8b1d81ceddcbb4697a6d92c2a99733` | Local showcase notebook source, executed output, or HTML rendering |
| `powerbi/dashboard_requirements.md` | 4,879 | `9a44d57d43eb0eca2baa8f84ea89b8bcc8e92b95acfe7db3c4919783a55325eb` | Power BI semantic-model, DAX, dashboard, or evidence contract |
| `powerbi/measures.dax` | 2,641 | `837397a46a2919c03e908e4896d64264ee163b289d6f2a46c91d7c8f29ad6df7` | Power BI semantic-model, DAX, dashboard, or evidence contract |
| `powerbi/README.md` | 877 | `82447ba611ad94a36e7cedc6866fe6fa1913219e5a6e50e02db7a6145b1bbab7` | Power BI semantic-model, DAX, dashboard, or evidence contract |
| `powerbi/semantic_model.md` | 4,692 | `9980b5fac5672ca9a9d3b655cd92d0e153ffded7f8b0cef876bb9eb09f05e1e9` | Power BI semantic-model, DAX, dashboard, or evidence contract |
| `PROJECT_COMPLETENESS_CHECKLIST.md` | 9,584 | `b97e48e5e654b56932b47c5e63a43a2cba7b8c6abb017524644bf458aa779226` | Package and external-environment completion gates |
| `pyproject.toml` | 608 | `c0c0405c36e17243183a5406d5d76984a998d7bdf823e018d4cf5bde267eb8dd` | Python package, pytest, and lint configuration |
| `README.md` | 11,992 | `38df87dbf61e15f0299fc0569651acfaf71566e98dee279e660c758331d5bb71` | Project overview, run order, evidence boundary, and navigation |
| `requirements-dev.txt` | 114 | `69ed298661c19f8a14fa0032baedfb431ac9472706073e065aaf7a62de087856` | Pinned-range Python dependency declaration |
| `requirements.txt` | 243 | `0b74d5174d4d9a845a35867ca6b402c2a6e69d311f115e51caf5d89ac606049e` | Pinned-range Python dependency declaration |
| `run_artifacts/.gitkeep` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Keeps an intentionally empty directory in Git |
| `run_artifacts/validation_report.txt` | 2,370 | `6d2707a23552e96a63e5657053b428fd15399730784923408b21c38ea2ac2d72` | Project support artifact |
| `scripts/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Project support artifact |
| `scripts/data_generation/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Deterministic fictional source-data generation code |
| `scripts/data_generation/generate_northstar_data.py` | 35,502 | `60c57a5a1122fbcf8ac0b22054999748c05126720061881c5a6df7775473e8a5` | Deterministic fictional source-data generation code |
| `scripts/documentation/__init__.py` | 61 | `659a39dcb4d24cb09cac88831e8623bb854a1efe34e56c6fde8a160ec606e63c` | Reproducible documentation and manifest generator |
| `scripts/documentation/generate_file_manifest.py` | 6,300 | `227cf9ea29984459bc13409b6d4c50707ee2284ddc31060988221dd276775766` | Reproducible documentation and manifest generator |
| `scripts/documentation/generate_metadata_docs.py` | 15,518 | `2b59d549af38f55d5aa2d580ac74254c4699a1110ce6027439a4def5ca68a652` | Reproducible documentation and manifest generator |
| `scripts/extraction/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Full and incremental local source extraction code |
| `scripts/extraction/extract_local_sources.py` | 12,430 | `9a52270d87d4d3e995679508e599cb1707def9c0859cafe73913463f7cdf32a2` | Full and incremental local source extraction code |
| `scripts/loading/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Source or serving-warehouse loading code |
| `scripts/loading/load_gold_to_sqlserver.py` | 12,358 | `93d4eb49b89ffc33d62cb523b9cc05cb093987fdbecb7e9da342dd7c0abe4f08` | Source or serving-warehouse loading code |
| `scripts/loading/load_postgres_source.py` | 3,501 | `58057cc60a7d522026f3b324c6f6227a8293ff237588da5a9928fd62ec3e9b2e` | Source or serving-warehouse loading code |
| `scripts/loading/load_sqlserver_source.py` | 3,767 | `d4c1c1367da0f9c4d2cda2ee7fb48a85cd2db71da68c9db83f51096e99aded70` | Source or serving-warehouse loading code |
| `scripts/local_demo/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Locally executable pandas parity implementation of the Gold model |
| `scripts/local_demo/build_local_gold.py` | 45,552 | `dc8e7bf8de4b9500f3af2b62a36f7737f3e4fd9986ecda5872658d1262070b53` | Locally executable pandas parity implementation of the Gold model |
| `scripts/setup/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Local tool verification helper |
| `scripts/setup/verify_local_tools.ps1` | 810 | `ce296af7fdc29531a816c463d2748e28e0ed7ac2a2c5e66659866f41e5c0f5de` | Local tool verification helper |
| `scripts/utilities/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Shared configuration, database, checksum, or logging utility |
| `scripts/utilities/checksums.py` | 509 | `3c5f0aa516e025dba2875102b1ecd8e42a5d429c396e9fe0b71b5b173d9f4798` | Shared configuration, database, checksum, or logging utility |
| `scripts/utilities/config.py` | 2,626 | `6885789d1e37157d77bb9a30df38e785d3630d1c2bb5849e635357c67a4cd4e3` | Shared configuration, database, checksum, or logging utility |
| `scripts/utilities/database.py` | 2,976 | `b7de582be357098da1556da78a2eff8aa8df242c4a5e2e750b2daefb4e9b5f53` | Shared configuration, database, checksum, or logging utility |
| `scripts/utilities/logging_utils.py` | 1,492 | `b6176e8c9abd49708475de665383f59e258731509d345f27817ed1f8343c63b5` | Shared configuration, database, checksum, or logging utility |
| `scripts/validation/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Static, data, notebook, link, secret, or project-contract validator |
| `scripts/validation/check_required_files.py` | 4,919 | `07eaec1ea7923cdd4ab194d237311518a0eb0d0200c4a54e81fa908ed33211c6` | Static, data, notebook, link, secret, or project-contract validator |
| `scripts/validation/scan_secrets.py` | 1,280 | `9a96ba278394b9a37a61cdbd35a3caeae0fcb9c65de565602d0785f6c63e51e6` | Static, data, notebook, link, secret, or project-contract validator |
| `scripts/validation/validate_generated_data.py` | 1,448 | `25496d4ef7406d4010b3cecc5b836231c5ca695628ed4457c02a455fda424828` | Static, data, notebook, link, secret, or project-contract validator |
| `scripts/validation/validate_markdown_links.py` | 1,407 | `d98855e9e9fe70d82f0ce193cf7cf0fb1a450342f8a68cef0b7a79e9aeec6acf` | Static, data, notebook, link, secret, or project-contract validator |
| `scripts/validation/validate_notebooks.py` | 985 | `2434be9f17cf28c2398cf28dcebebb28be741de8ae57ff917786d11cce736204` | Static, data, notebook, link, secret, or project-contract validator |
| `scripts/validation/validate_project_assets.py` | 13,860 | `9bd192f90afbbf0ed9fe80e521b054d54388bc58c221b9dab38a6920ef170826` | Static, data, notebook, link, secret, or project-contract validator |
| `scripts/validation/validate_sql_dialects.py` | 733 | `996c1ed5b039d7fed575b65f2146d5e94c156bad9946472f680a0ffb7d842870` | Static, data, notebook, link, secret, or project-contract validator |
| `sql/databricks/bronze/01_bronze_audit_pattern.sql` | 378 | `2f3258f9d04b2ce1dae0bb3702b8b4e187453de770a5ed87a51981ee2727da9c` | Databricks SQL reference pattern for medallion, quality, or KPI logic |
| `sql/databricks/gold/01_scd2_merge_pattern.sql` | 551 | `6bc8107306c027d139148490a941313cc9ddf4618252929036b721038083f883` | Databricks SQL reference pattern for medallion, quality, or KPI logic |
| `sql/databricks/gold/02_kpi_views.sql` | 559 | `20cf8bccd04ba3cea99d82deab5aa59a798d6f3f1827004387027f518531461b` | Databricks SQL reference pattern for medallion, quality, or KPI logic |
| `sql/databricks/quality/01_quality_gate.sql` | 423 | `6e8aa2f477f70725a473adf9c137b236c6a9bd79d4466964c752f6134121fc0c` | Databricks SQL reference pattern for medallion, quality, or KPI logic |
| `sql/databricks/silver/01_customer_quality_patterns.sql` | 522 | `7b954b51aa815a0b69b5ecbf5049307809dca7c03c84e284668d0395bb9390fc` | Databricks SQL reference pattern for medallion, quality, or KPI logic |
| `sql/databricks/silver/02_sales_quality_patterns.sql` | 491 | `886ff52a386a2147d6c7b94d9e81a5ab952b63a7d0f9b6e1e8e25cc6f0ee04ef` | Databricks SQL reference pattern for medallion, quality, or KPI logic |
| `sql/postgres/source/00_create_database.sql` | 298 | `7d8ebad0f2800ac892b1bd4de5aa64c9ef998fd8b2efae1cb23deaea0fdb2bcd` | PostgreSQL digital/marketing source DDL |
| `sql/postgres/source/01_create_digital_schema.sql` | 4,523 | `b924da412d7f77e86a9517c8e7da8dc84a118c685597b5f759683c7978b913c1` | PostgreSQL digital/marketing source DDL |
| `sql/postgres/validation/01_validate_digital_source.sql` | 941 | `781ba6abe548bb0da8237f5a4d9a05ddae48a372af39b667603650c2eb299579` | PostgreSQL source verification queries |
| `sql/sqlserver/analytics/20_analyst_questions.sql` | 9,115 | `fb905d8532db2dea183b8f07a75df2141b73ed1a1675fe323ade6614293bbc1c` | Analyst and KPI validation queries |
| `sql/sqlserver/analytics/kpi_validation_queries.sql` | 1,613 | `1c1c16971d832afd29dbfb69542b495897d90ceaa3c05ee87f4b81344dfc8f28` | Analyst and KPI validation queries |
| `sql/sqlserver/source/01_create_erp_database.sql` | 1,382 | `e5d80bff33c2367febfca74df2c5de24e3b82e4391f4242b08a45d5180e7c15e` | SQL Server ERP source database/schema/table DDL |
| `sql/sqlserver/source/02_create_erp_tables.sql` | 11,832 | `43261a6b21c06d0aac13566e1700b240d887b4515f5bed333c668f9aeecc2425` | SQL Server ERP source database/schema/table DDL |
| `sql/sqlserver/validation/01_validate_erp_source.sql` | 1,337 | `72da7e8ac675ae68ae8aa41d91b783cfac49448b0bbe168454c6e9e22261afe8` | SQL Server source or warehouse verification queries |
| `sql/sqlserver/validation/02_validate_warehouse.sql` | 1,195 | `caf14b4c5bc4dba91775c6779add266fa67ab1c381ee9adbc6e3940928336a1f` | SQL Server source or warehouse verification queries |
| `sql/sqlserver/warehouse/01_create_warehouse.sql` | 19,928 | `866cb7cf4d79fd6e82fa111122adb3f6245c11ad55d3fd240d8257801199b553` | SQL Server dimensional serving-warehouse DDL or semantic views |
| `sql/sqlserver/warehouse/02_create_staging_tables.sql` | 937 | `785f54db75b4498adf017f3b76e9b9c1902c79c4c09e594cc06e616ad5439037` | SQL Server dimensional serving-warehouse DDL or semantic views |
| `sql/sqlserver/warehouse/03_semantic_views.sql` | 1,576 | `e2302f60b3f5e28353a252c614fcac037b567b5bcc0beb64073e67e6d4e858b6` | SQL Server dimensional serving-warehouse DDL or semantic views |
| `tests/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Automated unit, integration, quality, or reconciliation test |
| `tests/data_quality/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Automated unit, integration, quality, or reconciliation test |
| `tests/data_quality/test_sample_quality_fixture.py` | 904 | `a879773c8e767b066b9a515e9f01d0241ad2e97c98cefb36a40895a1b3337168` | Automated unit, integration, quality, or reconciliation test |
| `tests/integration/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Automated unit, integration, quality, or reconciliation test |
| `tests/integration/test_completed_project.py` | 4,645 | `602b3bf1e506ae924c5307a11ebb622fb5145fe89f30d36a6ecd2e58ea5b2db8` | Automated unit, integration, quality, or reconciliation test |
| `tests/integration/test_repository_contract.py` | 872 | `3bb3ffe62b8cc2958870d62459c204c90f74738fd1c0efa82000535fa9b4c0dd` | Automated unit, integration, quality, or reconciliation test |
| `tests/reconciliation/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Automated unit, integration, quality, or reconciliation test |
| `tests/reconciliation/test_sample_reconciliation.py` | 794 | `2ad4c39bc8d85427eaa3975db33d326ed876d31ef741f5901ccf99364d2649e7` | Automated unit, integration, quality, or reconciliation test |
| `tests/unit/__init__.py` | 39 | `61391a19fd19659a67c1ac916e470a9764e95988ac111021b8ffd437641fbb7f` | Automated unit, integration, quality, or reconciliation test |
| `tests/unit/test_generator.py` | 1,403 | `072f2081af193a1ba9fda9b319e9e28c3d1af055d5f889a0a238c5e729df5b49` | Automated unit, integration, quality, or reconciliation test |
| `tests/unit/test_incremental_contracts.py` | 3,264 | `8892a4d9ced3969f630e50a9f108a8923e9dfeddb8b158bb92da94eeb73ce935` | Automated unit, integration, quality, or reconciliation test |

## Recreate this manifest

From the repository root, run:

```bash
python -m scripts.documentation.generate_file_manifest
```

Regenerating the manifest changes its generated timestamp and may change hashes when project files change.
