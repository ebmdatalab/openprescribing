  WITH chapters AS (
  SELECT
    *
  FROM
    frontend_section
  WHERE
    bnf_section IS NULL
    AND is_current IS TRUE),
  sections AS (
  SELECT
    *
  FROM
    frontend_section
  WHERE
    bnf_para IS NULL
    AND bnf_section IS NOT NULL
    AND is_current IS TRUE),
  paras AS (
  SELECT
    *
  FROM
    frontend_section
  WHERE
    bnf_para IS NOT NULL
    AND is_current IS TRUE)

SELECT
  chapters.name AS chapter_name,
  chapters.bnf_id AS chapter_id,
  sections.name AS section_name,
  sections.bnf_id AS section_id,
  paras.name AS para_name,
  paras.bnf_id AS para_id,
  chemicals.chem_name AS chemical_name,
  chemicals.bnf_code AS chemical_id,
  products.name AS product_name,
  products.bnf_code AS product_id,
  presentations.name AS presentation_name,
  presentations.bnf_code AS presentation_id,
  COALESCE(presentations.bnf_code, products.bnf_code, chemicals.bnf_code, paras.bnf_id, sections.bnf_id, chapters.bnf_id) AS unique_id,
  COALESCE(presentations.name, products.name, chemicals.chem_name, paras.name, sections.name, chapters.name) AS unique_name,
  products.is_generic AS is_generic,
  CASE char_length(COALESCE(presentations.bnf_code, products.bnf_code, chemicals.bnf_code, paras.bnf_id, sections.bnf_id, chapters.bnf_id))
  WHEN 2 THEN 'chapter'
  WHEN 4 THEN 'section'
  WHEN 6 THEN 'paragraph'
  WHEN 9 THEN 'chemical'
  WHEN 11 THEN 'product'
  ELSE 'presentation'
  END AS level
FROM
  frontend_presentation AS presentations
RIGHT JOIN
  frontend_product AS products
ON
  (SUBSTRING(presentations.bnf_code,
      0,
      12) = products.bnf_code)
RIGHT JOIN
  frontend_chemical AS chemicals
ON
  (SUBSTRING(products.bnf_code,
      0,
      10) = chemicals.bnf_code)
RIGHT JOIN
 paras
ON
 (SUBSTRING(chemicals.bnf_code,
      0,
      7) = paras.bnf_id)
RIGHT JOIN
  sections
ON
  (paras.bnf_section = sections.bnf_section
    AND paras.bnf_chapter = sections.bnf_chapter)
RIGHT JOIN
  chapters
ON
  (sections.bnf_chapter = chapters.bnf_chapter)
WHERE replaced_by_id IS NULL  -- only current presentations
AND (
    COALESCE(presentations.name, products.name, chemicals.chem_name, paras.name, sections.name, chapters.name) ILIKE %s
    )
ORDER BY
  presentation_name, product_name, chemical_name, para_name, section_name, chapter_name;
