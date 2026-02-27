import { GatsbyNode } from "gatsby";
import path from "path";
import { validatePaperFrontmatter, getQualityTier } from "./src/utils/validation";
import { calculateReadingTime } from "./src/utils/readingTime";

// Define GraphQL schema types for custom fields
export const createSchemaCustomization: GatsbyNode["createSchemaCustomization"] = ({ actions }) => {
  const { createTypes } = actions;

  createTypes(`
    type MdxFields {
      slug: String!
      qualityTier: String
      readingTime: Float
      wordCount: Int
    }

    type MdxFrontmatter {
      title: String!
      arxiv_id: String!
      authors: [String!]!
      published_date: Date! @dateformat
      go_live_date: Date! @dateformat
      kappa: Float!
      rsn_score: String!
      R: Float!
      S: Float!
      N: Float!
      tags: [String!]!
      primary_topic: String!
      difficulty: String!
      abstract: String!
      tldr: String
      arxiv_url: String!
      pdf_url: String
      github_url: String
      status: String!
      featured: Boolean
    }
  `);
};

export const onCreateNode: GatsbyNode["onCreateNode"] = ({
  node,
  actions,
  getNode,
}) => {
  const { createNodeField } = actions;

  if (node.internal.type === "Mdx") {
    const parent = getNode(node.parent as string);
    const sourceInstanceName = parent?.sourceInstanceName as string;

    // Create slug from file path
    const relativePath = parent?.relativePath as string;
    const slug = `/${sourceInstanceName}/${relativePath.replace(/\.mdx?$/, "")}`;

    createNodeField({
      node,
      name: "slug",
      value: slug,
    });

    // Validate frontmatter for review papers
    if (sourceInstanceName === "reviews" && node.frontmatter) {
      const frontmatter = node.frontmatter as any;

      // Run validation
      const validation = validatePaperFrontmatter(frontmatter);

      if (!validation.valid) {
        console.error(`\n❌ Invalid frontmatter in ${relativePath}:`);
        validation.errors.forEach(err => console.error(`   - ${err}`));
        throw new Error(`Frontmatter validation failed for ${relativePath}`);
      }

      // Log warnings (don't fail build)
      if (validation.warnings.length > 0) {
        console.warn(`\n⚠️  Warnings for ${relativePath}:`);
        validation.warnings.forEach(warn => console.warn(`   - ${warn}`));
      }

      // Add quality tier computed field
      if (typeof frontmatter.kappa === "number") {
        createNodeField({
          node,
          name: "qualityTier",
          value: getQualityTier(frontmatter.kappa),
        });
      }

      // Calculate reading time from content
      if (node.internal.content) {
        const readingTime = calculateReadingTime(node.internal.content);

        createNodeField({
          node,
          name: "readingTime",
          value: readingTime.minutes,
        });

        createNodeField({
          node,
          name: "wordCount",
          value: readingTime.words,
        });
      }
    }
  }
};

export const createPages: GatsbyNode["createPages"] = async ({
  graphql,
  actions,
  reporter,
}) => {
  const { createPage } = actions;

  // Query for MDX review pages
  const result = await graphql<{
    allMdx: {
      nodes: Array<{
        id: string;
        fields: { slug: string };
        internal: { contentFilePath: string };
      }>;
    };
  }>(`
    query {
      allMdx {
        nodes {
          id
          fields {
            slug
          }
          internal {
            contentFilePath
          }
        }
      }
    }
  `);

  if (result.errors) {
    reporter.panicOnBuild("Error loading MDX result", result.errors);
    return;
  }

  const reviewTemplate = path.resolve("./src/templates/review.tsx");

  result.data?.allMdx.nodes.forEach((node) => {
    createPage({
      path: node.fields.slug,
      component: `${reviewTemplate}?__contentFilePath=${node.internal.contentFilePath}`,
      context: {
        id: node.id,
      },
    });
  });
};
