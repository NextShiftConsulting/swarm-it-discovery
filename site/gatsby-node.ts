import { GatsbyNode } from "gatsby";
import path from "path";

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
