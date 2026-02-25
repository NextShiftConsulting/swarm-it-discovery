import type { GatsbyConfig } from "gatsby";

const config: GatsbyConfig = {
  siteMetadata: {
    title: "Swarm-It Research Discovery",
    description: "AI-curated analysis of cutting-edge ML/AI research papers",
    siteUrl: "https://swarmit.nextshiftconsulting.com",
    author: "Next Shift Consulting",
  },
  plugins: [
    "gatsby-plugin-image",
    "gatsby-plugin-sharp",
    "gatsby-transformer-sharp",
    {
      resolve: "gatsby-plugin-mdx",
      options: {
        extensions: [".mdx", ".md"],
      },
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "posts",
        path: `${__dirname}/../content/generated-posts`,
      },
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "topics",
        path: `${__dirname}/../content/topics`,
      },
    },
  ],
};

export default config;
